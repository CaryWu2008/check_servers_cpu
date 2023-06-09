import csv
import os
import time
from datetime import datetime

import sys
sys.path.insert(0, '/var/www/myapp')
from myapp import app

output_file = '/var/www/template/resource.log'
server_info_file = '/var/www/template/server_info.csv'

def send_email(server_name, cpu_usage):
    sender = 'itsd@lisuantech.com'
    receivers = 'carywu@lisuantech.com'
    subject = f'High CPU usage on {server_name}'
    body = f'The CPU usage on {server_name} has been over 95% for the last 10 minutes. Current CPU usage: {cpu_usage}%'
    s_nail_command = f'echo "{body}" | s-nail -:/ -S mta=smtp://smtp.eda.sh -S from=itsd@lisuantech.com -s "{subject}" -r {sender} {receivers}'
    os.system(s_nail_command)


def check_servers():
    with open('server_list.txt', 'r') as f:
        servers = [line.strip() for line in f if line.strip()]
    high_cpu_count = {}
    server_info = {}
    while True:
        server_data = []
        for server in servers:
            try:
                cpu_usage = os.popen(f'ssh {server} top -bn1 | grep "%Cpu(s)" | awk \'{{print $2 + $4}}\'').read().strip()
                mem_usage = os.popen(f'ssh {server} free -m | awk \'NR==2{{printf "%.2f%%", $3*100/$2 }}\'').read().strip()
                if server not in server_info or datetime.now().date() != server_info[server]['date']:
                    cpu_cores = os.popen(f'ssh {server} lscpu -b -p=Core,Socket | grep -v "^#" | sort -u | wc -l').read().strip()
                    mem_total = os.popen(f'ssh {server} free -m | awk \'NR==2{{printf "%.1fGB", $2/1024}}\'').read().strip()
                    cpu_info = os.popen(f'ssh {server} lscpu | grep "Model name"').read().strip().split(':')[1].strip()
                    os_version = 'RHEL ' + os.popen(f'ssh {server} cat /etc/os-release | grep "VERSION_ID"').read().strip().split('=')[1].strip('"')
                    server_info[server] = {
                        'date': datetime.now().date(),
                        'cpu_cores': cpu_cores,
                        'mem_total': mem_total,
                        'cpu_info': cpu_info,
                        'os_version': os_version
                    }
                else:
                    cpu_cores = server_info[server]['cpu_cores']
                    mem_total = server_info[server]['mem_total']
                    cpu_info = server_info[server]['cpu_info']
                    os_version = server_info[server]['os_version']
            except:
                cpu_usage = 'failed'
                mem_usage = 'failed'
                cpu_cores = 'failed'
                mem_total = 'failed'
            server_data.append([server, cpu_cores, mem_total, cpu_usage, mem_usage])
            if float(cpu_usage) > 95:
                if server in high_cpu_count:
                    high_cpu_count[server] += 1
                else:
                    high_cpu_count[server] = 1
                if high_cpu_count[server] >= 10:
                    send_email(server, cpu_usage)
                    high_cpu_count[server] = 0
            else:
                high_cpu_count[server] = 0
        server_data.sort(key=lambda x: float(x[3]), reverse=True)
        with open(output_file, 'w') as f:
            f.write(f'Last updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write('-' * 70 + '\n')
            f.write(f'{"Server":<15}{"CPU Cores":<10}{"Memory Total":<15}{"CPU Usage":<12}{"Memory Usage":<15}\n')
            for data in server_data:
                if data[1] == 'failed':
                    f.write(f'{data[0]:<15}{data[1]:<10}{data[2]:<15}{data[3]:<12}{data[4]:<15}\n')
                else:
                    f.write(f'{data[0]:<15}{data[1]:<10}{data[2]:<15}{data[3]:<12}{data[4]:<15}\n')

        with open(server_info_file, 'w') as f:
            writer = csv.writer(f)
            writer.writerow(['Server', 'CPU Info', 'OS Version', 'Uptime', 'Users', 'Terminals'])
            for server in servers:
                # 获取服务器信息
                cpu_info = os.popen(f'ssh {server} lscpu | grep "Model name"').read().strip().split(':')[1].strip()
                os_version = 'RHEL ' + os.popen(f'ssh {server} cat /etc/os-release | grep "VERSION_ID"').read().strip().split('=')[1].strip('"')
                uptime = os.popen(f'ssh {server} uptime -p').read().strip()
                users = os.popen(f'ssh {server} who | wc -l').read().strip()
                terminals = os.popen(f'ssh {server} ps aux | grep sshd: | grep -v grep | wc -l').read().strip()
                writer.writerow([server, cpu_info, os_version, uptime, users, terminals])

        time.sleep(60)

if __name__ == '__main__':
    check_servers()
    app.run()
