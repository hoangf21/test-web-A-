import sqlite3 # Thư viện tương tác với cơ sở dữ liệu SQLite
from flask import Flask, request, jsonify, render_template # Flask dùng để tạo ứng dụng web
import googlemaps # Google Maps API để lấy dữ liệu chỉ đường
import heapq # Thư viện hỗ trợ hàng đợi ưu tiên, dùng trong thuật toán A*
import time # Thư viện thời gian, dùng để tính toán thời gian thực thi
from datetime import datetime # Thư viện hỗ trợ xử lý ngày giờ

app = Flask(__name__) # Khởi tạo ứng dụng Flask

# Khởi tạo client Google Maps API với API Key
gmaps = googlemaps.Client(key='AIzaSyBnJKzKGqg4qjRpV_zFdrOxIoB4mOlXKJU')

#Hàm Heuristic
def heuristic(a, b):
    """ Ước lượng chi phí giữa hai điểm (đơn giản là khoảng cách Euclidean). """
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

''' Thuật toán A* để tìm đường đi ngắn nhất trong đồ thị.'''
def a_star(start, goal, graph):
    #thuật toán này nhận vào 1 điểm start, điểm kết thúc goal và một đồ thị graph đại diện cho mạng lười đường đi (Các nút và đoạn nối giữa chúng)

    open_set = []# Khởi tạo danh sách mở(hay còn gọi là danh sách ưu tiên)

    #đây là danh sách ưu tiên (sử dụng heapq để đảm bảo luôn chọn điểm có giá trị f(n) nhỏ nhất. Ban đầu chỉ chứa 1 điểm bắt đầu
    heapq.heappush(open_set, (0, start)) #thêm điểm bắt đầu với f = 0 danh sách mở

    came_from = {} #dùng để lưu trữ đường đi ngược lại, giúp tìm ra đường đi sau khi đến được đích
    g_score = {start: 0} #chi phí từ điểm bắt đầu đến 1 nút cụ thể
    f_score = {start: heuristic(start, goal)} #chi phí dự đoán đi từ một điểm bắt đầu đến đích qua một nút cụ thể

    '''Vòng lặp chính'''
    while open_set:
        current = heapq.heappop(open_set)[1]
        #Chọn điểm có giá trị f(n) nhỏ nhất từ danh sách mở(open_set). Điểm này được lưu trong biến current
        if current == goal:
        #Kiểm tra nếu current là đích thì ta tìm được đường đi và cần phải truy vết lại để xây dựng đường đi
            path = []
            while current in came_from:
                path.append(current) #truy vết ngược lại từ đích về điểm bắt đầu
                current = came_from[current]
            path.append(start)
            path.reverse() #đảo ngược để có đường đi đúng từ start đến goal
            return path # Trả về đường đi đã tìm thấy

        #Nếu không phải đích, thuật toán sẽ tiếp tục kiểm tra các nút lân cận của nó
        for neighbor, cost in graph.get(current, []):
            tentative_g_score = g_score[current] + cost # Tính g(n) mới
            if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current # Cập nhật thông tin nếu có chi phí nhỏ hơn
                g_score[neighbor] = tentative_g_score #cập nhật g(n) cho neighbor
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal) # Cập nhật f(n) = g(n) + h(n)
                if neighbor not in [i[1] for i in open_set]:
                #Nếu nút lân cận chưa được xét hoặc chi phí mới nhỏ hơn chi phí trước đó, cập nhật lại thông tin và thêm vào danh sách mở
                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

    return []
    #sau khi tìm được đích, thuật toán sẽ truy ngược từ đích về điểm bắt đầu thông qua came_from và trả về đường đi tìm được



@app.route('/')
def index():
    return render_template('index.html') # Trả về file HTML trang chủ

@app.route('/saved_directions', methods=['GET'])
def saved_directions():
    conn = sqlite3.connect('directions.db') # Kết nối tới cơ sở dữ liệu
    cursor = conn.cursor() # Tạo con trỏ để thực hiện các truy vấn SQL

    # Truy vấn để lấy tất cả các chỉ đường đã lưu trong bảng "directions" và sắp xếp theo ID tăng dần
    cursor.execute('SELECT * FROM directions ORDER BY id ASC') # Lấy tất cả chỉ đường đã lưu
    directions = cursor.fetchall() # Lấy tất cả các dòng từ kết quả truy vấn
    conn.close() # Đóng kết nối
    return jsonify(directions) # Trả về kết quả dạng JSON

def decode_unicode(s):
    return s.encode().decode('unicode_escape')


@app.route('/delete_directions/<int:id>', methods=['DELETE'])
def delete_directions(id):
    conn = sqlite3.connect('directions.db')
    cursor = conn.cursor()


    cursor.execute('DELETE FROM directions WHERE id = ?', (id,)) # Xóa chỉ đường theo ID
    conn.commit()

    if cursor.rowcount > 0:
        conn.close()
        return jsonify({'message': 'Xóa thành công!'}), 200
    else:
        conn.close()
        return jsonify({'error': 'Không tìm thấy chỉ đường với ID này!'}), 404


# //Invoke-WebRequest -Uri http://localhost:5000/delete_all_directions -Method Delete


@app.route('/delete_all_directions', methods=['DELETE'])
def delete_all_directions():
    conn = sqlite3.connect('directions.db')
    cursor = conn.cursor()

    cursor.execute('DELETE FROM directions') # Xóa tất cả chỉ đường
    conn.commit()

    cursor.execute('DELETE FROM sqlite_sequence WHERE name="directions"') # Đặt lại ID

    conn.close()
    return jsonify({'message': 'Đã xóa tất cả dữ liệu thành công và ID đã được đặt lại!'}), 200

# Xây dựng một decorator để định nghĩa một router mới.
# Router này sẽ xử lý các yêu cầu của HTTP GET xuống đường dẫn là directions.
@app.route('/directions', methods=['GET'])
def directions():
# lấy và chuẩn bị thông tin cần thiết từ yêu cầu HTTP, bao gồm đị điểm bắt đầu, địa điểm kết thúc và cách thức di chuyển
    start = request.args.get('start')
    goal = request.args.get('goal')
    travelMode = request.args.get('travelMode').lower()
    time_start = time.time() #Khởi tạo địa điểm bắt đầu để tính thời gian chạy cảu thuật toán

    # Gọi Google Maps API để lấy dữ liệu chỉ đường
    directions_result = gmaps.directions(start, goal, travelMode, alternatives = True,)



    # Tính toán đường đi sử dụng A*


#  Phân tích kết quả từ Google Maps API và tạo ra một đồ thị.
    def parse_directions_to_graph(directions_result):

        graph = {}

        #tạo đồ thị rỗng, trong đó gồm  : Key(tọa độ của một điểm trên bản đồ) và value (là danh sách các nút lân cận(các điểm có thể đi đến nút hiện tại) và chi phí (khoảng cách)để đi đến điểm đó

        for route in directions_result:
            legs = route.get('legs', [])
            for leg in legs:
                steps = leg.get('steps', [])
                for step in steps:
                    start_location = (step['start_location']['lat'], step['start_location']['lng'])
                    end_location = (step['end_location']['lat'], step['end_location']['lng'])
                    distance = step['distance']['value']  # khoảng cách giữa hai điểm

                    # Thêm vào đồ thị
                    if start_location not in graph:
                        graph[start_location] = []
                    graph[start_location].append((end_location, distance))

                    # Thêm cho đồ thị theo chiều ngược lại (nếu cần thiết)
                    if end_location not in graph:
                        graph[end_location] = []
                    graph[end_location].append((start_location, distance))  # Giả sử có thể đi ngược lại

        return graph

    if directions_result:
        # Phân tích kết quả để tạo đồ thị
        # Bạn cần phải phân tích kết quả từ Google Maps API và chuyển đổi nó thành đồ thị cho A*
        graph = parse_directions_to_graph(directions_result)

        # Lấy tọa độ bắt đầu và kết thúc
        start_coordinates = (directions_result[0]['legs'][0]['start_location']['lat'],
                             directions_result[0]['legs'][0]['start_location']['lng'])
        goal_coordinates = (directions_result[0]['legs'][0]['end_location']['lat'],
                            directions_result[0]['legs'][0]['end_location']['lng'])

        path = a_star(start_coordinates, goal_coordinates, graph) # Tính toán đường đi sử dụng A*
        time_end = time.time()  # Khởi tạo thời gian kết thúc thuật toán
        print(f"Thoi gian chay cua thuat toan A* {time_end - time_start}")  # Thời gian chạy của thuật toán
        # Trích xuất thông tin khoảng cách và thời gian
        distance = directions_result[0]['legs'][0]['distance']['text']
        distance_value = directions_result[0]['legs'][0]['distance']['value']
        duration = directions_result[0]['legs'][0]['duration']['text']
        duration_value = directions_result[0]['legs'][0]['duration']['value']
        print(path)

        save_directions_to_db(start, goal, travelMode, distance, duration)
        # Trả về chỉ đường cùng với khoảng cách,lộ trình và thời gian
        return jsonify({
            'directions': directions_result,
            'distance': distance,
            'distance_value': distance_value,
            'duration': duration,
            'duration_value': duration_value,
            'path': path,  # Lộ trình tính được bằng A*
        })
    else:
        return jsonify({'error': 'Không tìm thấy chỉ đường'}), 404 #trả về lỗi nếu không có kết quả

#thêm thông tin tìm kiếm vào sqlite
def save_directions_to_db(start, goal, travel_mode, distance, duration):
    conn = sqlite3.connect('directions.db') # Kết nối cơ sở dữ liệu
    cursor = conn.cursor()
    # Lưu chỉ đường vào bảng directions
    cursor.execute('''
        INSERT INTO directions (start, goal, travel_mode, distance, duration)
        VALUES (?, ?, ?, ?, ?)
    ''', (start, goal, travel_mode, distance, duration))

    conn.commit() # Lưu thay đổi
    conn.close() # Đóng kết nối


if __name__ == '__main__':
    app.run(debug=True) # Chạy ứng dụng Flask ở chế độ debug
