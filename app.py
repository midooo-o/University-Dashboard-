import sqlite3
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask import render_template

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = sqlite3.connect('universities.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/")
def index():
    return render_template("dashboard.html")

@app.route("/api/insights")
def insights():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM Students")
        total_students = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM Courses")
        total_courses = cursor.fetchone()[0]

        cursor.execute("SELECT SUM(COALESCE(FeeAmount, 0)) FROM StudentFees")
        row_fees = cursor.fetchone()
        total_fees = round(float(row_fees[0]) if row_fees[0] else 0.0, 2)

        cursor.execute("SELECT AVG(Salary) FROM Professors")
        row_salary = cursor.fetchone()
        avg_salary = round(float(row_salary[0]) if row_salary[0] else 0.0, 2)
        
        cursor.close()
        conn.close()

        return jsonify({
            "total_students": total_students,
            "total_courses": total_courses,
            "total_fees": total_fees,
            "avg_salary": avg_salary
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/enrollment_by_year")
def enrollment_by_year():
    year_id = request.args.get("year")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT Y.YearName, COUNT(S.student_id) AS StudentCount
            FROM Students S
            JOIN Years Y ON S.Year_id = Y.Year_id
        """
        params = []
        if year_id:
            query += " WHERE Y.Year_id = ?"
            params.append(year_id)
            
        query += " GROUP BY Y.YearName ORDER BY Y.YearName"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/students_per_course")
def students_per_course():
    department = request.args.get("department")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT C.CourseName, COUNT(SC.student_id) AS StudentCount
            FROM StudentCourses SC
            JOIN Courses C ON SC.CourseID = C.CourseID
            LEFT JOIN Professors P ON C.ProfessorID = P.ProfessorID 
        """
        params = []
        if department and department != "All":
            query += " WHERE P.Department = ?"
            params.append(department)
            
        query += " GROUP BY C.CourseName ORDER BY StudentCount DESC"

        cursor.execute(query, params)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/fees_by_year")
def fees_by_year():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT Y.YearName, SUM(COALESCE(F.FeeAmount,0)) AS TotalFees
            FROM StudentFees F
            JOIN Students S ON F.student_id = S.student_id
            JOIN Years Y ON S.Year_id = Y.Year_id
            GROUP BY Y.YearName
            ORDER BY Y.YearName
        """)
        rows = cursor.fetchall()
        result = [{"YearName": row["YearName"], "TotalFees": round(float(row["TotalFees"]), 2)} for row in rows]
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/salary_by_department")
def salary_by_department():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(Department,'Unknown') AS Department, SUM(COALESCE(Salary,0)) AS TotalSalary
            FROM Professors
            GROUP BY Department
            ORDER BY TotalSalary DESC
        """)
        rows = cursor.fetchall()
        result = [{"Department": row["Department"], "TotalSalary": round(float(row["TotalSalary"]), 2)} for row in rows]
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/departments")
def departments():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT COALESCE(Department, 'Unknown') AS Department
            FROM Professors
            ORDER BY Department
        """)
        rows = cursor.fetchall()
        result = [row["Department"] for row in rows]
        result.insert(0, "All")
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/top_courses")
def top_courses():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT C.CourseName, COUNT(SC.student_id) AS StudentCount
            FROM StudentCourses SC
            JOIN Courses C ON SC.CourseID = C.CourseID
            GROUP BY C.CourseName
            ORDER BY StudentCount DESC
            LIMIT 5
        """)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/gender_distribution")
def gender_distribution():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(Gender, 'Unknown') AS Gender, COUNT(*) AS StudentCount
            FROM Students
            GROUP BY Gender
        """)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        cursor.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)