from pathlib import Path
path = Path('templates/dashboard.html')
path.write_text('''{% extends 'base.html' %}

{% block title %}Scholarship Dashboard | Richwell Colleges Inc.{% endblock %}

{% block content %}

<div class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow">Scholarship Management System</div>
    <h1>Your <span>Academic</span> Dashboard</h1>
    <p>Manage applications, track your progress, and explore scholarship opportunities.</p>
  </div>
</div>

<div class="section-label">Overview</div>
<div class="summary">
  <a class="summary-box" href="{% url 'applications:list' %}">
    <div class="summary-icon">📋</div>
    <h3>Total Applications</h3>
    <p>{{ total_applications }}</p>
  </a>

  <a class="summary-box" href="{% url 'applications:approved' %}">
    <div class="summary-icon">✅</div>
    <h3>Approved</h3>
    <p>{{ approved_count }}</p>
  </a>

  <a class="summary-box" href="{% url 'applications:pending' %}">
    <div class="summary-icon">⏳</div>
    <h3>Pending</h3>
    <p>{{ pending_count }}</p>
  </a>

  <a class="summary-box" href="{% url 'applications:rejected' %}">
    <div class="summary-icon">❌</div>
    <h3>Rejected</h3>
    <p>{{ rejected_count }}</p>
  </a>
</div>

<div class="section-label">Quick Actions</div>
<div class="cards">
  <div class="card">
    <span class="card-icon">🎓</span>
    <h3>Apply for Scholarship</h3>
    <p>Submit a new scholarship application and start your journey.</p>
    <a class="card-btn" href="{% url 'applications:create' %}">Apply Now</a>
  </div>

  <div class="card">
    <span class="card-icon">📄</span>
    <h3>My Applications</h3>
    <p>View, track, and manage all your submitted applications.</p>
    <a class="card-btn" href="{% url 'applications:list' %}">View All</a>
  </div>

  <div class="card">
    <span class="card-icon">👤</span>
    <h3>My Student Profile</h3>
    <p>Track your scholarship status and student records.</p>
    <a class="card-btn" href="{% url 'users:profile' %}">Open Profile</a>
  </div>
</div>

<div class="section-label">Recent Applications</div>
<div class="table-container">
  <div class="table-header">
    <h3>Application History</h3>
    <a href="{% url 'applications:list' %}">View all</a>
  </div>

  <table>
    <thead>
      <tr>
        <th>Scholarship</th>
        <th>Date Applied</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for app in applications %}
      <tr>
        <td>{{ app.scholarship.name }}</td>
        <td class="date-cell">{{ app.created_at|date:'F j, Y' }}</td>
        <td><span class="status {{ app.status }}">{{ app.status|title }}</span></td>
      </tr>
      {% empty %}
      <tr class="empty-row">
        <td colspan="3">No applications found. Start by applying for a scholarship above.</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% endblock %}
''', encoding='utf-8')
print('wrote', path)
