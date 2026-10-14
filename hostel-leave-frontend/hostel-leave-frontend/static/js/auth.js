// Handles both the login and register forms.

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");
const message = document.getElementById("message");

function readForm(form) {
  return Object.fromEntries(new FormData(form));
}

if (loginForm) {
  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(message, "");
    try {
      const result = await api("/api/login", "POST", readForm(loginForm));
      window.location.href = result.redirect;
    } catch (err) {
      setMessage(message, err.message);
    }
  });
}

if (registerForm) {
  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    setMessage(message, "");
    try {
      await api("/api/register", "POST", readForm(registerForm));
      setMessage(message, "Account created. Taking you to log in…", "success");
      setTimeout(() => (window.location.href = "/login"), 1000);
    } catch (err) {
      setMessage(message, err.message);
    }
  });
}
