# CodeCommit Repository

resource "aws_codecommit_repository" "main" {
  repository_name = var.project_name
  description     = "ChatGepeto - Educational AI Assistant"

  tags = {
    Name = "${var.project_name}-repo"
  }
}
