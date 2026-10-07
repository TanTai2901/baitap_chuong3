import csv
import io
from html import escape
from flask import (
    Flask,
    abort,
    make_response,
    redirect,
    render_template_string,
    request,
    url_for,
)

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.json.ensure_ascii = False

STUDENTS = {
    "23T1020001": {
        "name": "Nguyễn Văn An",
        "lop": "K47A",
        "scores": {"PMMNM": 8.5, "CSDL": 7.0, "MMT": 9.0},
    },
    "23T1020002": {
        "name": "Trần Thị Bình",
        "lop": "K47A",
        "scores": {"PMMNM": 6.0, "CSDL": 5.5, "MMT": 9.0},
    },
    "23T1020003": {
        "name": "Lê Hoàng Cường",
        "lop": "K47B",
        "scores": {"PMMNM": 9.5, "CSDL": 9.0, "MMT": 7.0},
    },
    "23T1020004": {
        "name": "Phạm Minh Dũng",
        "lop": "K47B",
        "scores": {"PMMNM": 4.0, "CSDL": 3.5, "MMT": 5.0},
    },
    "23T1020005": {
        "name": "Hoàng Thu Hà",
        "lop": "K47A",
        "scores": {},
    },
    "23T1020006": {
        "name": "Võ Quốc Khánh",
        "lop": "K47C",
        "scores": {"PMMNM": 7.5, "MMT": 8.0},
    },
}


def average(scores):
    if not scores:
        return None
    return round(sum(scores.values()) / len(scores), 2)


def rank(avg):
    if avg is None:
        return "Chưa có điểm"
    if avg >= 8.5:
        return "Giỏi"
    if avg >= 7.0:
        return "Khá"
    if avg >= 5.0:
        return "Trung bình"
    return "Yếu"


def student_summary(mssv):
    student = STUDENTS[mssv]
    avg = average(student["scores"])
    return {
        "mssv": mssv,
        "name": student["name"],
        "lop": student["lop"],
        "scores": student["scores"],
        "average": avg,
        "rank": rank(avg),
    }


def layout(title, body):
    escaped_title = escape(title)
    return f"""<!text/html>
<html>
<head>
    <meta charset="utf-8">
    <title>{escaped_title} - Sổ điểm</title>
</head>
<body>
    <nav>
        <a href="{url_for('index')}">Trang chủ</a> |
        <a href="{url_for('student_list')}">Sinh viên</a> |
        <a href="{url_for('search')}">Tìm kiếm sinh viên</a>
    </nav>
    <hr>
    <h1>{escaped_title}</h1>
    {body}
</body>
</html>"""


@app.route("/")
def index():
    total_students = len(STUDENTS)
    classes = len({s["lop"] for s in STUDENTS.values()})
    body = f"""
    <p>Tổng số sinh viên: {total_students}</p>
    <p>Số lớp: {classes}</p>
    <p>
        <a href="{url_for('student_list')}">Xem danh sách sinh viên (Web)</a><br>
        <a href="{url_for('api_student_list')}">Xem API danh sách sinh viên (JSON)</a>
    </p>
    """
    return layout("Trang chủ", body)


@app.route("/students")
def student_list():
    lop_filter = request.args.get("lop", "").strip().lower()
    all_classes = sorted(list({s["lop"] for s in STUDENTS.values()}))

    filter_links = [f'<a href="{url_for("student_list")}">Tất cả</a>']
    for c in all_classes:
        filter_links.append(f'<a href="{url_for("student_list", lop=c)}">{escape(c)}</a>')
    filter_bar = " | ".join(filter_links)

    filtered_students = []
    for mssv, info in STUDENTS.items():
        if not lop_filter or info["lop"].lower() == lop_filter:
            filtered_students.append(student_summary(mssv))

    if not filtered_students:
        body = f"{filter_bar}<br><br><p>Không có sinh viên phù hợp.</p>"[cite: 8]
        return layout("Danh sách sinh viên", body)

    rows = []
    for s in filtered_students:
        avg_str = f"{s['average']:.2f}" if s["average"] is not None else "-"[cite: 8]
        detail_url = url_for("student_detail", mssv=s["mssv"])
        rows.append(
            f"<tr>"
            f"<td><a href='{detail_url}'>{escape(s['mssv'])}</a></td>"
            f"<td>{escape(s['name'])}</td>"
            f"<td>{escape(s['lop'])}</td>"
            f"<td>{avg_str}</td>"
            f"<td>{escape(s['rank'])}</td>"
            f"</tr>"
        )

    table = f"""
    {filter_bar}<br><br>
    <table border="1" cellpadding="5">
        <tr>
            <th>MSSV</th><th>Họ tên</th><th>Lớp</th><th>Điểm TB</th><th>Xếp loại</th>
        </tr>
        {"".join(rows)}
    </table>
    """
    return layout("Danh sách sinh viên", table)


@app.route("/students/<mssv>")
def student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")[cite: 9]

    summary = student_summary(mssv)
    lop_url = url_for("student_list", lop=summary["lop"])
    export_url = url_for("export_csv", mssv=mssv)
    short_url = url_for("short_link", mssv=mssv)

    scores_rows = [f"<tr><td>{escape(c)}</td><td>{s}</td></tr>" for c, s in summary["scores"].items()]
    scores_table = (
        f"<table border='1' cellpadding='5'><tr><th>Học phần</th><th>Điểm</th></tr>{''.join(scores_rows)}</table>"
        if scores_rows else "<p>Chưa có điểm học phần nào.</p>"
    )
    avg_str = f"{summary['average']:.2f}" if summary["average"] is not None else "-"

    body = f"""
    <p><b>MSSV:</b> {escape(summary['mssv'])}</p>
    <p><b>Họ tên:</b> {escape(summary['name'])}</p>
    <p><b>Lớp:</b> <a href="{lop_url}">{escape(summary['lop'])}</a></p>
    <p><b>Điểm TB:</b> {avg_str} | <b>Xếp loại:</b> {escape(summary['rank'])}</p>
    <p><b>Link rút gọn:</b> <a href="{short_url}">{short_url}</a></p>
    <p><a href="{export_url}">Tải bảng điểm (CSV)</a></p>
    <h3>Bảng điểm</h3>
    {scores_table}
    """
    return layout("Chi tiết sinh viên", body)


@app.route("/sv/<mssv>")
def short_link(mssv):
    return redirect(url_for("student_detail", mssv=mssv), code=301)[cite: 9]


@app.route("/students/<mssv>/export")
def export_csv(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không có sinh viên với MSSV = {mssv}.")[cite: 10]

    student = STUDENTS[mssv]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["hoc_phan", "diem"])[cite: 10]
    for course, score in student["scores"].items():
        writer.writerow([course, score])

    response = make_response(output.getvalue())[cite: 10]
    response.headers["Content-Type"] = "text/csv; charset=utf-8"[cite: 10]
    response.headers["Content-Disposition"] = f"attachment; filename=diem_{mssv}.csv"[cite: 10]
    return response


@app.route("/search")
def search():
    q = request.args.get("q", "")
    escaped_q = escape(q)
    results = []

    if q:
        q_lower = q.lower()
        for mssv, info in STUDENTS.items():
            if q_lower in mssv.lower() or q_lower in info["name"].lower():[cite: 11]
                results.append(student_summary(mssv))

    result_html = ""
    if q:
        result_html += f"<p>Tìm thấy {len(results)} kết quả cho \"{escaped_q}\"</p><ul>"[cite: 11]
        for s in results:
            url = url_for("student_detail", mssv=s["mssv"])
            result_html += f'<li><a href="{url}">{escape(s["mssv"])} - {escape(s["name"])}</a> ({escape(s["lop"])})</li>'[cite: 11]
        result_html += "</ul>"

    body = f"""
    <form action="{url_for('search')}" method="get">
        <input type="text" name="q" value="{escaped_q}">
        <button type="submit">Tìm kiếm</button>
    </form>
    {result_html}
    """
    return layout("Tìm kiếm", body)


@app.route("/api/students", methods=["GET"])
def api_student_list():
    lop = request.args.get("lop", "").strip().lower()

    min_avg_raw = request.args.get("min_avg")
    min_avg = None
    if min_avg_raw is not None:
        try:
            min_avg = float(min_avg_raw)
        except ValueError:
            abort(400, description="Tham số min_avg phải là một số.")[cite: 13]

    res = []
    for mssv in STUDENTS:
        s = student_summary(mssv)
        if lop and s["lop"].lower() != lop:[cite: 13]
            continue
        if min_avg is not None:
            if s["average"] is None or s["average"] < min_avg:[cite: 13]
                continue
        res.append(s)

    return res


@app.route("/api/students/<mssv>", methods=["GET"])
def api_student_detail(mssv):
    if mssv not in STUDENTS:
        abort(404, description=f"Không tìm thấy sinh viên với MSSV = {mssv}")[cite: 13]
    return student_summary(mssv)


@app.route("/api/students/<mssv>/scores/<course>", methods=["GET", "PUT", "DELETE"])
def api_student_score(mssv, course):
    if mssv not in STUDENTS:
        abort(404, description=f"Không tìm thấy sinh viên với MSSV = {mssv}")[cite: 14]

    course_code = course.upper()[cite: 14]
    scores = STUDENTS[mssv]["scores"]

    if request.method == "GET":[cite: 14]
        if course_code not in scores:
            abort(404, description=f"Sinh viên chưa có điểm học phần {course_code}")[cite: 14]
        return {"mssv": mssv, "course": course_code, "score": scores[course_code]}[cite: 14]

    elif request.method == "PUT":[cite: 14]
        score_raw = request.args.get("score")
        if score_raw is None:
            abort(400, description="Thiếu tham số score")[cite: 14]

        try:
            score = float(score_raw)
        except ValueError:
            abort(400, description="Tham số score phải là kiểu số")[cite: 14]

        if not (0 <= score <= 10):[cite: 14]
            abort(400, description="Điểm phải nằm trong khoảng [0, 10]")[cite: 14]

        is_new = course_code not in scores
        scores[course_code] = score
        avg = average(scores)

        body = {
            "mssv": mssv,
            "course": course_code,
            "score": score,
            "average": avg,
        }

        if is_new:
            res = make_response(body, 201)[cite: 14]
            res.headers["Location"] = url_for("api_student_score", mssv=mssv, course=course_code)[cite: 14]
            return res
        return body, 200[cite: 14]

    elif request.method == "DELETE":[cite: 14]
        if course_code not in scores:
            abort(404, description=f"Không tìm thấy điểm học phần {course_code} để xóa")[cite: 14]
        del scores[course_code]
        return "", 204[cite: 14]


ERR_TITLES = {
    400: "Dữ liệu không hợp lệ",[cite: 16]
    404: "Không tìm thấy",[cite: 16]
    405: "Phương thức không được hỗ trợ",[cite: 16]
}


@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(405)
def handle_error(error):
    code = error.code
    title = ERR_TITLES.get(code, "Lỗi")
    description = getattr(error, "description", str(error))

    if request.path.startswith("/api/"):
        return {"error": title, "detail": description}, code

    body = f"<p><b>Mã lỗi:</b> {code}</p><p><b>Mô tả:</b> {escape(description)}</p>"
    return layout(f"{code} - {title}", body), code


if __name__ == "__main__":
    app.run(port=8000, debug=True)