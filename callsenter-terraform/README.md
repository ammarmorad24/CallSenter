# CallSenter Terraform Deployment

This project contains Terraform configurations for deploying the CallSenter application, which includes three EC2 instances: a customer client, an agent client, and a chat service. Each instance is configured to run the necessary setup scripts to ensure they are ready for use.

## Project Structure

- **main.tf**: The main Terraform configuration file that defines the resources for the EC2 instances, including their AMI, instance type, and security group settings.
- **variables.tf**: This file defines the input variables for the Terraform configuration, such as instance types and AMI IDs.
- **outputs.tf**: Specifies the output values from the Terraform configuration, including the public IP addresses of the deployed EC2 instances.
- **scripts/**: Contains startup scripts for each EC2 instance:
  - **customer_client_setup.sh**: Setup commands for the customer client instance.
  - **agent_client_setup.sh**: Setup commands for the agent client instance.
  - **chat_service_setup.sh**: Setup commands for the chat service instance.
- **.gitignore**: Specifies files and directories to be ignored by Git, such as Terraform state files.
- **README.md**: Documentation for the project.

## Deployment Instructions

1. **Install Terraform**: Ensure that Terraform is installed on your local machine. You can download it from the [Terraform website](https://www.terraform.io/downloads.html).

2. **Configure AWS Credentials**: Make sure your AWS credentials are configured. You can set them up using the AWS CLI or by creating a `~/.aws/credentials` file.

3. **Clone the Repository**: Clone the CallSenter repository to your local machine.

4. **Navigate to the Project Directory**: Change to the directory where the Terraform files are located.

5. **Initialize Terraform**: Run the following command to initialize the Terraform configuration:
   ```
   terraform init
   ```

6. **Plan the Deployment**: Generate an execution plan to see what resources will be created:
   ```
   terraform plan
   ```

7. **Apply the Configuration**: Deploy the infrastructure by running:
   ```
   terraform apply
   ```

8. **Access the Instances**: Once the deployment is complete, you can access the EC2 instances using their public IP addresses.

## Additional Information

- Ensure that the security group "launch lizard 4" is properly configured to allow necessary traffic to and from the instances.
- Review the setup scripts in the `scripts` directory for any additional configuration that may be required for your specific use case.

This README provides a high-level overview of the project and instructions for deploying the infrastructure using Terraform. For more detailed information, refer to the individual Terraform files and scripts.