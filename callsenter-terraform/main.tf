resource "aws_instance" "customer_client" {
  ami           = var.customer_client_ami
  instance_type = var.instance_type
  security_groups = ["launch_lizard_4"]

  user_data = file("scripts/customer_client_setup.sh")

  tags = {
    Name = "Customer Client"
  }
}

resource "aws_instance" "agent_client" {
  ami           = var.agent_client_ami
  instance_type = var.instance_type
  security_groups = ["launch_lizard_4"]

  user_data = file("scripts/agent_client_setup.sh")

  tags = {
    Name = "Agent Client"
  }
}

resource "aws_instance" "chat_service" {
  ami           = var.chat_service_ami
  instance_type = var.instance_type
  security_groups = ["launch_lizard_4"]

  user_data = file("scripts/chat_service_setup.sh")

  tags = {
    Name = "Chat Service"
  }
}

output "customer_client_public_ip" {
  value = aws_instance.customer_client.public_ip
}

output "agent_client_public_ip" {
  value = aws_instance.agent_client.public_ip
}

output "chat_service_public_ip" {
  value = aws_instance.chat_service.public_ip
}