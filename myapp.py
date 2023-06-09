from flask import Flask, render_template
import csv

app = Flask(__name__, template_folder='/var/www/template')

output_file = '/var/www/template/resource.log'
server_info_file = '/var/www/template/server_info.csv'

@app.route('/')
def index():
    data = []
    with open(output_file, 'r') as f:
        lines = f.readlines()
        data.append(lines[0].strip().split(': ')[1])
        for line in lines[3:]:
            if line.strip():
                row = line.strip().split()
                data.append(row)

    server_info = {}
    with open(server_info_file, 'r') as f:
        reader = csv.reader(f)
        next(reader)  # 跳过标题行
        for row in reader:
            server_info[row[0]] = row[1:]

    return render_template('index.html', data=data, server_info=server_info)

if __name__ == '__main__':
    app.run()
