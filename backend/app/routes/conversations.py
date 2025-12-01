"""Conversation API endpoints."""
import json

from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_login import login_required, current_user

from ..extensions import db, csrf
from ..models import Conversation, Message, Citation
from ..schemas import ConversationSchema, ConversationDetailSchema, MessageSchema
from ..services import (
    RAGService,
    process_attachment,
    get_base64_for_image,
    extract_text_from_doc,
)

bp = Blueprint('conversations', __name__, url_prefix='/api/conversations')


@bp.route('/', methods=['GET'])
@login_required
def list_conversations():
    """List user's conversations."""
    query = Conversation.query.filter_by(user_id=current_user.id)

    # Search filter
    search = request.args.get('q')
    if search:
        query = query.filter(
            db.or_(
                Conversation.title.ilike(f'%{search}%'),
                Conversation.messages.any(Message.content.ilike(f'%{search}%'))
            )
        )

    conversations = query.order_by(Conversation.updated_at.desc()).all()
    return jsonify({'results': ConversationSchema(many=True).dump(conversations)})


@bp.route('/', methods=['POST'])
@login_required
@csrf.exempt
def create_conversation():
    """Create a new conversation."""
    data = request.get_json() or {}
    title = data.get('title', '')

    conversation = Conversation(
        user_id=current_user.id,
        title=title
    )
    db.session.add(conversation)
    db.session.commit()

    return jsonify(ConversationSchema().dump(conversation)), 201


@bp.route('/<int:id>/', methods=['GET'])
@login_required
def get_conversation(id):
    """Get conversation with messages."""
    conversation = Conversation.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()
    return jsonify(ConversationDetailSchema().dump(conversation))


@bp.route('/<int:id>/', methods=['PATCH'])
@login_required
@csrf.exempt
def update_conversation(id):
    """Update conversation."""
    conversation = Conversation.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()

    data = request.get_json() or {}
    if 'title' in data:
        conversation.title = data['title']

    db.session.commit()
    return jsonify(ConversationSchema().dump(conversation))


@bp.route('/<int:id>/', methods=['DELETE'])
@login_required
@csrf.exempt
def delete_conversation(id):
    """Delete conversation."""
    conversation = Conversation.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()

    db.session.delete(conversation)
    db.session.commit()

    return '', 204


@bp.route('/<int:id>/messages/', methods=['POST'])
@login_required
@csrf.exempt
def send_message(id):
    """Send a message and get AI response."""
    conversation = Conversation.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()

    # Handle content from form-data or JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        user_message_content = request.form.get('content', '')
        files = request.files.getlist('files')
    else:
        data = request.get_json() or {}
        user_message_content = data.get('content', '')
        files = []

    if not user_message_content.strip() and not files:
        return jsonify({'error': 'Message content or files required'}), 400

    try:
        # Process file attachments
        attachments = []
        images_base64 = []
        doc_context = ""

        for file in files:
            try:
                attachment = process_attachment(file, current_user.id)
                attachments.append(attachment)

                if attachment['category'] == 'image':
                    images_base64.append(get_base64_for_image(attachment['file_path']))
                else:
                    extracted = extract_text_from_doc(
                        attachment['file_path'],
                        attachment['file_type']
                    )
                    if extracted:
                        doc_context += f"\n[Attached: {attachment['filename']}]\n{extracted}\n"
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

        # Append extracted document text to message content
        full_content = user_message_content
        if doc_context:
            full_content += doc_context

        # Create user message
        user_message = Message(
            conversation=conversation,
            role='user',
            content=full_content,
            attachments=attachments
        )
        db.session.add(user_message)
        db.session.commit()

        # Auto-title conversation if this is the first message
        if conversation.messages.count() == 1 and not conversation.title:
            try:
                rag_service = RAGService()
                title = rag_service.generate_conversation_title(user_message_content)
                conversation.title = title
                db.session.commit()
            except Exception:
                conversation.title = user_message_content[:50]
                db.session.commit()

        # Get conversation history for context
        conversation_history = []
        previous_messages = conversation.messages.filter(
            Message.id != user_message.id
        ).order_by(Message.created_at).limit(10).all()

        for msg in previous_messages:
            conversation_history.append({
                'role': msg.role,
                'content': msg.content
            })

        # RAG pipeline
        rag_service = RAGService()

        # Retrieve relevant chunks
        relevant_chunks = rag_service.retrieve_relevant_chunks(
            query=user_message_content,
            user_id=current_user.id,
            top_k=5
        )

        # Build context
        context = rag_service.build_context_from_chunks(relevant_chunks)

        # Generate AI response
        ai_response_content = rag_service.generate_response(
            user_message=user_message_content,
            context=context,
            conversation_history=conversation_history,
            images=images_base64 if images_base64 else None
        )

        # Create assistant message
        assistant_message = Message(
            conversation=conversation,
            role='assistant',
            content=ai_response_content
        )
        db.session.add(assistant_message)
        db.session.commit()

        # Create citations
        for chunk, relevance_score in relevant_chunks:
            citation = Citation(
                message=assistant_message,
                chunk=chunk,
                relevance_score=relevance_score
            )
            db.session.add(citation)
        db.session.commit()

        return jsonify({
            'user_message': MessageSchema().dump(user_message),
            'assistant_message': MessageSchema().dump(assistant_message)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to process message: {str(e)}'}), 500


@bp.route('/<int:id>/messages/stream/', methods=['POST'])
@login_required
@csrf.exempt
def send_message_stream(id):
    """Send a message and stream the AI response via SSE."""
    conversation = Conversation.query.filter_by(
        id=id, user_id=current_user.id
    ).first_or_404()

    data = request.get_json() or {}
    user_message_content = data.get('content', '').strip()

    if not user_message_content:
        return jsonify({'error': 'Message content required'}), 400

    def generate_sse():
        try:
            # Create user message
            user_message = Message(
                conversation=conversation,
                role='user',
                content=user_message_content
            )
            db.session.add(user_message)
            db.session.commit()

            # Send user message event
            user_msg_data = MessageSchema().dump(user_message)
            yield f"event: user_message\ndata: {json.dumps(user_msg_data)}\n\n"

            # Auto-title if first message
            if conversation.messages.count() == 1 and not conversation.title:
                try:
                    rag_service = RAGService()
                    title = rag_service.generate_conversation_title(user_message_content)
                    conversation.title = title
                    db.session.commit()
                except Exception:
                    conversation.title = user_message_content[:50]
                    db.session.commit()

            # Get conversation history
            conversation_history = []
            previous_messages = conversation.messages.filter(
                Message.id != user_message.id
            ).order_by(Message.created_at).limit(10).all()

            for msg in previous_messages:
                conversation_history.append({
                    'role': msg.role,
                    'content': msg.content
                })

            # RAG pipeline
            rag_service = RAGService()
            relevant_chunks = rag_service.retrieve_relevant_chunks(
                query=user_message_content,
                user_id=current_user.id,
                top_k=5
            )
            context = rag_service.build_context_from_chunks(relevant_chunks)

            # Build messages for LLM
            system_prompt = f"""You are ChatGepeto, a helpful AI assistant that answers questions based on provided documents.

Context from documents:
{context}

Instructions:
- Answer the user's question using the context provided above
- If the context doesn't contain relevant information, say so clearly
- Be concise and accurate
- Cite specific documents when referencing information"""

            messages = [{"role": "system", "content": system_prompt}]
            if conversation_history:
                for msg in conversation_history[-10:]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            messages.append({"role": "user", "content": user_message_content})

            # Stream response
            full_response = ""
            for chunk in rag_service.llm.chat_stream(
                messages,
                temperature=0.7,
                max_tokens=500
            ):
                full_response += chunk
                yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"

            # Create assistant message
            assistant_message = Message(
                conversation=conversation,
                role='assistant',
                content=full_response
            )
            db.session.add(assistant_message)
            db.session.commit()

            # Create citations
            for chunk, relevance_score in relevant_chunks:
                citation = Citation(
                    message=assistant_message,
                    chunk=chunk,
                    relevance_score=relevance_score
                )
                db.session.add(citation)
            db.session.commit()

            # Send final message with citations
            assistant_msg_data = MessageSchema().dump(assistant_message)
            yield f"event: assistant_message\ndata: {json.dumps(assistant_msg_data)}\n\n"
            yield f"event: done\ndata: {json.dumps({'status': 'complete'})}\n\n"

        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

    response = Response(
        stream_with_context(generate_sse()),
        content_type='text/event-stream'
    )
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response
