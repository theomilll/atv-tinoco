# ECS Cluster and Service (Fargate)

resource "aws_ecs_cluster" "main" {
  name = "${var.project_name}-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "${var.project_name}-cluster"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "main" {
  family                   = var.project_name
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.backend_cpu + var.frontend_cpu
  memory                   = var.backend_memory + var.frontend_memory
  execution_role_arn       = aws_iam_role.ecs_task_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = "${aws_ecr_repository.backend.repository_url}:latest"
      cpu       = var.backend_cpu
      memory    = var.backend_memory
      essential = true

      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]

      environment = [
        {
          name  = "FLASK_ENV"
          value = "production"
        },
        {
          name  = "DATABASE_URL"
          value = "sqlite:////app/data/chatgepeto.db"
        },
        {
          name  = "CORS_ALLOWED_ORIGINS"
          value = "*"
        }
      ]

      secrets = concat(
        [
          {
            name      = "OLLAMA_HOST"
            valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/chatgepeto/ollama-host"
          },
          {
            name      = "OLLAMA_MODEL"
            valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/chatgepeto/ollama-model"
          }
        ],
        var.groq_api_key != "" ? [
          {
            name      = "GROQ_API_KEY"
            valueFrom = aws_ssm_parameter.groq_api_key[0].arn
          },
          {
            name      = "SECRET_KEY"
            valueFrom = aws_ssm_parameter.secret_key[0].arn
          }
        ] : []
      )

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "backend"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/api/health/ || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    },
    {
      name      = "frontend"
      image     = "${aws_ecr_repository.frontend.repository_url}:latest"
      cpu       = var.frontend_cpu
      memory    = var.frontend_memory
      essential = true

      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]

      environment = []

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "frontend"
        }
      }

      dependsOn = [
        {
          containerName = "backend"
          condition     = "HEALTHY"
        }
      ]
    }
  ])

  tags = {
    Name = "${var.project_name}-task"
  }
}

# SSM Parameters for secrets (optional)
resource "aws_ssm_parameter" "groq_api_key" {
  count = var.groq_api_key != "" ? 1 : 0

  name        = "/${var.project_name}/groq-api-key"
  description = "Groq API Key"
  type        = "SecureString"
  value       = var.groq_api_key

  tags = {
    Name = "${var.project_name}-groq-api-key"
  }
}

resource "aws_ssm_parameter" "secret_key" {
  count = var.secret_key != "" ? 1 : 0

  name        = "/${var.project_name}/secret-key"
  description = "Flask Secret Key"
  type        = "SecureString"
  value       = var.secret_key

  tags = {
    Name = "${var.project_name}-secret-key"
  }
}

# Additional IAM policy for SSM access
resource "aws_iam_role_policy" "ecs_ssm_access" {
  name = "${var.project_name}-ecs-ssm-access"
  role = aws_iam_role.ecs_task_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter"
        ]
        Resource = concat(
          [
            "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/chatgepeto/ollama-host",
            "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/chatgepeto/ollama-model"
          ],
          var.groq_api_key != "" ? [
            aws_ssm_parameter.groq_api_key[0].arn,
            aws_ssm_parameter.secret_key[0].arn
          ] : []
        )
      }
    ]
  })
}

# ECS Service
resource "aws_ecs_service" "main" {
  name            = "${var.project_name}-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = aws_subnet.public[*].id
    security_groups  = [aws_security_group.ecs.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.backend.arn
    container_name   = "backend"
    container_port   = 8000
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.frontend.arn
    container_name   = "frontend"
    container_port   = 3000
  }

  depends_on = [
    aws_lb_listener.http
  ]

  tags = {
    Name = "${var.project_name}-service"
  }
}
