from flask import Flask, render_template, jsonify
import requests
import csv

output_file = '/var/www/home.eda.sh/templates/resource.log'
server_info_file = '/var/www/home.eda.sh/templates/server_info.csv'

def get_data_from_files():
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
        try:
            next(reader)  # 跳过标题行
            for row in reader:
                server_info[row[0]] = row[1:]
        except StopIteration:
            pass

    return data, server_info

app = Flask(__name__)

@app.route('/')
def index():
    data, server_info = get_data_from_files()
    return render_template('index.html', data=data, server_info=server_info)

@app.route('/get_data')
def get_data():
    data, server_info = get_data_from_files()
    return jsonify(data=data, server_info=server_info)

if __name__ == '__main__':
    app.run()
