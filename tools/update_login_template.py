from pathlib import Path
content = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Scholarship Login | Richwell Colleges Inc.</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;600;700&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">

<style>
  :root {
    --purple:    #3b0764;
    --purple-mid:#5b21b6;
    --gold:      #c9a227;
    --gold-light:#e6c96e;
    --cream:     #fdf8f0;
    --text-dark: #1a0a2e;
    --text-muted:#7c6e8a;
    --border:    #e8dff5;
    --white:     #ffffff;
  }

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  html, body { min-height: 100%; }

  body {
    font-family: 'DM Sans', sans-serif;
    background: radial-gradient(circle at top left, rgba(255,255,255,0.24), transparent 28%),
                radial-gradient(circle at bottom right, rgba(201,162,39,0.15), transparent 25%),
                linear-gradient(180deg, #0e0434 0%, #210044 60%, #3b0764 100%);
    color: var(--white);
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    overflow-x: hidden;
  }

  body::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.95' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.08'/%3E%3C/svg%3E");
    pointer-events: none;
    opacity: 0.35;
    z-index: 0;
  }

  .login-wrapper {
    position: relative;
    z-index: 1;
    width: min(980px, 100%);
    display: grid;
    grid-template-columns: 1.1fr 1fr;
    border-radius: 28px;
    overflow: hidden;
    box-shadow: 0 40px 90px rgba(0,0,0,0.45);
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.14);
    backdrop-filter: blur(14px);
  }

  .panel-left,
  .panel-right {
    position: relative;
    overflow: hidden;
  }

  .panel-left {
    padding: 56px 44px;
    background: linear-gradient(160deg, rgba(59,7,100,0.98) 0%, rgba(30,5,64,0.96) 100%);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }

  .panel-left::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(circle at 20% 20%, rgba(201,162,39,0.12), transparent 28%),
                radial-gradient(circle at 80% 80%, rgba(255,255,255,0.08), transparent 18%);
    pointer-events: none;
  }

  .brand-area {
    position: relative;
    z-index: 1;
  }

  .brand-seal {
    width: 58px; height: 58px;
    display: grid;
    place-items: center;
    background: linear-gradient(135deg, var(--gold), var(--gold-light));
    border-radius: 16px;
    box-shadow: 0 16px 30px rgba(255,207,91,0.18);
    margin-bottom: 22px;
    font-size: 26px;
  }

  .brand-school {
    position: relative;
    z-index: 1;
    font-family: 'Cormorant Garamond', serif;
    font-size: 24px;
    font-weight: 700;
    color: var(--white);
    line-height: 1.12;
    margin-bottom: 6px;
  }

  .brand-system {
    position: relative;
    z-index: 1;
    font-size: 12px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: rgba(255,255,255,0.72);
  }

  .panel-tagline {
    position: relative;
    z-index: 1;
    margin-top: 34px;
  }

  .panel-tagline blockquote {
    font-family: 'Cormorant Garamond', serif;
    font-size: 34px;
    line-height: 1.2;
    color: #fff;
    margin: 0 0 18px;
  }

  .panel-tagline blockquote span {
    color: var(--gold-light);
  }

  .panel-tagline p {
    max-width: 340px;
    font-size: 15px;
    line-height: 1.75;
    color: rgba(255,255,255,0.8);
  }

  .panel-features {
    position: relative;
    z-index: 1;
    display: grid;
    gap: 12px;
    margin-top: 30px;
  }

  .feature-pill {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px;
    border-radius: 14px;
    background: rgba(255,255,255,0.08);
    color: rgba(255,255,255,0.9);
    font-size: 13px;
  }

  .panel-right {
    background: var(--cream);
    padding: 52px 44px;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }

  .form-eyebrow {
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 10px;
  }

  .form-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 36px;
    font-weight: 700;
    color: var(--text-dark);
    margin-bottom: 12px;
    line-height: 1.05;
  }

  .form-subtitle {
    font-size: 14px;
    color: var(--text-muted);
    margin-bottom: 34px;
    max-width: 460px;
  }

  .field-group {
    margin-bottom: 18px;
  }

  .field-group label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
  }

  .field-group input,
  input[type="text"],
  input[type="password"],
  input[type="email"] {
    width: 100%;
    padding: 14px 16px;
    border: 1.5px solid var(--border);
    border-radius: 14px;
    background: var(--white);
    font-size: 14px;
    color: var(--text-dark);
    transition: border-color 0.2s, box-shadow 0.2s;
    outline: none;
  }

  .field-group input:focus {
    border-color: var(--purple-mid);
    box-shadow: 0 0 0 4px rgba(91,33,182,0.08);
  }

  .captcha-row {
    margin-bottom: 18px;
  }

  .captcha-row label {
    display: block;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text-muted);
    margin-bottom: 8px;
  }

  .captcha-row img {
    width: 100%;
    max-width: 100%;
    border-radius: 14px;
    margin-bottom: 12px;
    border: 1px solid var(--border);
  }

  .captcha-row input {
    width: 100%;
    padding: 14px 16px;
    border: 1.5px solid var(--border);
    border-radius: 14px;
    background: var(--white);
    font-size: 14px;
    color: var(--text-dark);
    transition: border-color 0.2s, box-shadow 0.2s;
    outline: none;
  }

  .btn-login {
    width: 100%;
    padding: 15px 18px;
    margin-top: 10px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--purple), var(--purple-mid), var(--gold));
    color: var(--white);
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 0.3px;
    cursor: pointer;
    transition: transform 0.2s ease, box-shadow 0.3s ease;
    box-shadow: 0 16px 28px rgba(59,7,100,0.18);
  }

  .btn-login:hover {
    transform: translateY(-1px);
    box-shadow: 0 20px 38px rgba(59,7,100,0.22);
  }

  .divider {
    display: flex;
    align-items: center;
    gap: 12px;
    margin: 28px 0 20px;
    color: var(--text-muted);
    font-size: 12px;
  }

  .divider::before,
  .divider::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--border);
  }

  .form-footer {
    font-size: 13px;
    color: var(--text-muted);
    text-align: center;
  }

  .form-footer a {
    color: var(--purple);
    font-weight: 700;
    text-decoration: none;
    border-bottom: 1px solid transparent;
    transition: border-color 0.2s, color 0.2s;
  }

  .form-footer a:hover {
    color: var(--gold);
    border-color: var(--gold);
  }

  .messages-list {
    margin-bottom: 18px;
    padding: 0;
    list-style: none;
  }

  .messages-list li {
    padding: 12px 14px;
    border-radius: 14px;
    margin-bottom: 10px;
    font-size: 13px;
  }

  .messages-list li.error   { background: #fee2e2; color: #991b1b; }
  .messages-list li.success { background: #d1fae5; color: #065f46; }
  .messages-list li.warning { background: #fef3c7; color: #92400e; }

  .errorlist {
    margin: 8px 0 0;
    padding: 0;
    list-style: none;
  }

  .errorlist li {
    font-size: 12px;
    color: #b91c1c;
    margin-top: 6px;
  }

  .errorlist li::before { content: '⚠ '; }

  @media (max-width: 860px) {
    body { padding: 18px; }
    .login-wrapper { display: flex; flex-direction: column; width: 100%; }
    .panel-left { display: none; }
    .panel-right { padding: 34px 24px; }
  }
</style>
</head>

<body>

<div class="login-wrapper">

  <div class="panel-left">
    <div class="brand-area">
      <div class="brand-seal">🎓</div>
      <div class="brand-school">Richwell Colleges Inc.</div>
      <div class="brand-system">Scholarship Portal</div>
    </div>

    <div class="panel-tagline">
      <blockquote>Empowering <span>scholars</span> to shape tomorrow.</blockquote>
      <p>Access your scholarship opportunities, track your applications, and build your academic future with a secure student portal.</p>
    </div>

    <div class="panel-features">
      <span class="feature-pill">Secure sign-in</span>
      <span class="feature-pill">CAPTCHA protection</span>
      <span class="feature-pill">Fast application tracking</span>
    </div>
  </div>

  <div class="panel-right">
    <div class="form-eyebrow">Student Access</div>
    <h1 class="form-title">Welcome Back</h1>
    <p class="form-subtitle">Sign in to your scholarship account to continue and manage your application progress.</p>

    {% if messages %}
    <ul class="messages-list">
      {% for message in messages %}
      <li class="{{ message.tags }}">{{ message }}</li>
      {% endfor %}
    </ul>
    {% endif %}

    <form action="{% url 'security:login' %}" method="POST">
      {% csrf_token %}

      <div class="field-group">
        <label for="{{ form.username.id_for_label }}">Username</label>
        {{ form.username }}
        {{ form.username.errors }}
      </div>

      <div class="field-group">
        <label for="{{ form.password.id_for_label }}">Password</label>
        {{ form.password }}
        {{ form.password.errors }}
      </div>

      <div class="captcha-row">
        <label>Verification</label>
        {{ form.captcha }}
        {{ form.captcha.errors }}
      </div>

      <button class="btn-login" type="submit">Sign In</button>
    </form>

    <div class="divider">or</div>

    <div class="form-footer">
      New applicant? <a href="{% url 'applications:create' %}">Apply for a Scholarship</a>
    </div>
  </div>
</div>

</body>
</html>
'''
Path('security/templates/login.html').write_text(content, encoding='utf-8')
print('wrote security/templates/login.html')
