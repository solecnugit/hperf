import paramiko

# trans = paramiko.Transport(("ampere01.solelab.tech", 22))

# trans.connect(username="tongyu", password="19990203jkl")

# client = paramiko.SSHClient

client = paramiko.SSHClient()

client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

client.connect(hostname="ampere01.solelab.tech", port=22, username="tongyu", password="19990203jkl")

# _, stdout, _ = client.exec_command("ls")

# output = stdout.read()
# print(output.decode("utf-8"))

# _, stdout, _ = client.exec_command("cd /home")

# output = stdout.read()
# print(output.decode("utf-8"))

_, stdout, _ = client.exec_command("mkdir ~/.hperf/")

print(type(stdout))
print(type(stdout.channel))

ret_code = stdout.channel.recv_exit_status()
print("returned code:", ret_code)
output = stdout.read().decode("utf-8")
print(output)

sftp = client.open_sftp()

dirlist = sftp.listdir(".")
print(type(dirlist))
print(dirlist)

print(sftp.getcwd())
sftp.chdir("./.hperf/")
print(sftp.getcwd())
# sftp.remove("a")
print(sftp.listdir())
with sftp.open("b.txt", "w+") as f:
    f.write("Hello,\nWorld\n")

for file in sftp.listdir("."):
    print(file)


client.close()