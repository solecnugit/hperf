import paramiko

client = paramiko.SSHClient()

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

client.connect(hostname="ampere01.solelab.tech", port=22, username="tongyu", password="19990203jkl")

stdin, stdout, stderr = client.exec_command("ls")

output = stdout.read()

print(output.decode("utf-8"))

client.close()