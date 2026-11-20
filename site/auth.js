const API_URL = "http://89.127.206.24:5000";

const loginTab = document.getElementById("loginTab");
const registerTab = document.getElementById("registerTab");

const loginForm = document.getElementById("loginForm");
const registerForm = document.getElementById("registerForm");

const message = document.getElementById("message");


function showMessage(text, success = false) {
    message.textContent = text;
    message.style.color = success ? "#a8ff00" : "#ff4545";
}


loginTab.addEventListener("click", () => {
    loginForm.classList.remove("hidden");
    registerForm.classList.add("hidden");

    loginTab.classList.add("active");
    registerTab.classList.remove("active");

    showMessage("");
});


registerTab.addEventListener("click", () => {
    registerForm.classList.remove("hidden");
    loginForm.classList.add("hidden");

    registerTab.classList.add("active");
    loginTab.classList.remove("active");

    showMessage("");
});


// Вход в аккаунт

loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    try {
        const response = await fetch(`${API_URL}/api/login`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: document.getElementById("loginUsername").value,
                password: document.getElementById("loginPassword").value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.error || "Ошибка входа");
            return;
        }

        showMessage("Вход выполнен! Перенаправляем...", true);

        setTimeout(() => {
            window.location.href = "account.html";
        }, 1000);

    } catch (error) {
        showMessage("Не удалось связаться с сервером");
    }
});


// Регистрация

registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const password = document.getElementById("regPassword").value;
    const passwordConfirm = document.getElementById("regPasswordConfirm").value;

    if (password !== passwordConfirm) {
        showMessage("Пароли не совпадают!");
        return;
    }

    try {
        const response = await fetch(`${API_URL}/api/register`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username: document.getElementById("regUsername").value,
                full_name: document.getElementById("regFullName").value,
                password: password,
                password_confirm: passwordConfirm,
                phone: document.getElementById("regPhone").value,
                email: document.getElementById("regEmail").value
            })
        });

        const data = await response.json();

        if (!response.ok) {
            showMessage(data.error || "Ошибка регистрации");
            return;
        }

        showMessage("Аккаунт создан! Перенаправляем...", true);

        setTimeout(() => {
            window.location.href = "account.html";
        }, 1000);

    } catch (error) {
        showMessage("Не удалось связаться с сервером");
    }
});