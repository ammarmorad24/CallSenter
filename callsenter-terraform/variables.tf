variable "customer_client_instance_type" {
  description = "The instance type for the customer client EC2 instance"
  type        = string
  default     = "t3.micro"
}

variable "agent_client_instance_type" {
  description = "The instance type for the agent client EC2 instance"
  type        = string
  default     = "t3.micro"
}

variable "chat_service_instance_type" {
  description = "The instance type for the chat service EC2 instance"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "The AMI ID to use for the EC2 instances"
  type        = string
}

variable "security_group_id" {
  description = "The security group ID for the EC2 instances"
  type        = string
  default     = "launch-lizard-4"
}

variable "key_name" {
  description = "The key pair name to use for SSH access to the instances"
  type        = string
}