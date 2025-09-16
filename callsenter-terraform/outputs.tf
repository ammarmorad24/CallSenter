output "customer_client_public_ip" {
  value = aws_instance.customer_client.public_ip
}

output "agent_client_public_ip" {
  value = aws_instance.agent_client.public_ip
}

output "chat_service_public_ip" {
  value = aws_instance.chat_service.public_ip
}