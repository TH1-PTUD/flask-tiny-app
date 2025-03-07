@app.route('/admin')
def admin():
    if session.get('role') != 'admin':
        flash("Truy cập trái phép!", "danger")
        return redirect(url_for('home'))

    # Phân trang cho admin
    page_admin = request.args.get('page_admin', 1, type=int)
    per_page = 8  
    offset_user = (page_admin - 1) * per_page
    with sqlite3.connect(DATABASE) as conn:
        c = conn.cursor()
        # Tổng số bài viết của người dùng hiện tại
        c.execute("SELECT COUNT(*) FROM posts WHERE username != ?", (session['username'],))
        total_user_posts = c.fetchone()[0]
        total_user_pages = (total_user_posts + per_page - 1) // per_page

        c.execute("SELECT * FROM users WHERE username != ? ORDER BY user_id DESC LIMIT ? OFFSET ?",
                  (session['username'], per_page, offset_user))
        users = c.fetchall()
    return render_template('admin.html', users=users,
                           page_admin=page_admin,
                           total_user_pages=total_user_pages,)