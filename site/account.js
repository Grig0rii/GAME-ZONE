const API_URL = "http://89.127.206.24:5000";

async function loadBookings() {
    const response = await fetch(`${API_URL}/api/bookings`, {
        credentials: "include"
    });

    if (!response.ok) {
        throw new Error("Не удалось загрузить бронирования");
    }

    const bookings = await response.json();
    const container = document.querySelector(".booking-card");

    if (!container) {
        throw new Error("Не найден блок бронирований");
    }

    container.innerHTML = "";

    if (bookings.length === 0) {
        const message = document.createElement("p");
        message.textContent = "Пока у тебя нет бронирований.";
        container.appendChild(message);

        const link = document.createElement("a");
        link.href = "booking.html";
        link.textContent = "ЗАБРОНИРОВАТЬ МЕСТО →";
        container.appendChild(link);

        return;
    }

    bookings.forEach(booking => {
        const item = document.createElement("div");
        item.className = "booking-item";

        const title = document.createElement("h3");
        title.textContent = booking.place;
        item.appendChild(title);

        const details = [
            `Дата: ${booking.date}`,
            `Начало: ${booking.start_time}`,
            `Окончание: ${booking.end_time}`,
            `Статус: ${booking.status === "cancelled" ? "Отменено" : "Активно"}`
        ];

        details.forEach(text => {
            const p = document.createElement("p");
            p.textContent = text;
            item.appendChild(p);
        });

        if (booking.status === "active") {
            const cancellationStatus = document.createElement("p");
            cancellationStatus.className = "cancel-booking-info";

            if (booking.cancel_allowed === true) {
                cancellationStatus.textContent = "Отмена бронирования: РАЗРЕШЕНА";
                item.appendChild(cancellationStatus);

                if (booking.cancel_deadline) {
                    const deadline = document.createElement("p");
                    deadline.textContent =
                        "Отменить можно до: " +
                        new Date(booking.cancel_deadline).toLocaleString("ru-RU");

                    item.appendChild(deadline);
                }

                const button = document.createElement("button");
                button.className = "cancel-booking-button";
                button.textContent = "ОТМЕНИТЬ БРОНЬ";

                button.addEventListener("click", async () => {
                    if (!confirm("Ты действительно хочешь отменить это бронирование?")) {
                        return;
                    }

                    button.disabled = true;
                    button.textContent = "ОТМЕНЯЕМ...";

                    try {
                        const cancelResponse = await fetch(
                            `${API_URL}/api/bookings/${booking.id}/cancel`,
                            {
                                method: "POST",
                                credentials: "include"
                            }
                        );

                        const result = await cancelResponse.json();

                        if (!cancelResponse.ok) {
                            alert(
                                result.message ||
                                result.error ||
                                "Не удалось отменить бронирование"
                            );

                            button.disabled = false;
                            button.textContent = "ОТМЕНИТЬ БРОНЬ";
                            return;
                        }

                        alert("Бронирование успешно отменено!");
                        await loadBookings();

                    } catch (error) {
                        console.error("Ошибка отмены:", error);
                        alert("Ошибка соединения с сервером");

                        button.disabled = false;
                        button.textContent = "ОТМЕНИТЬ БРОНЬ";
                    }
                });

                item.appendChild(button);

            } else {
                cancellationStatus.textContent =
                    "Отмена бронирования: ЗАПРЕЩЕНА. " +
                    (booking.cancel_reason || "Сейчас отменить бронь нельзя.");

                item.appendChild(cancellationStatus);
            }

        } else if (booking.status === "cancelled") {
            const cancelledMessage = document.createElement("p");
            cancelledMessage.className = "cancel-booking-info";
            cancelledMessage.textContent = "Это бронирование уже отменено.";
            item.appendChild(cancelledMessage);
        }

        container.appendChild(item);
    });
}


// TELEGRAM: проверка и отображение статуса

function showTelegramMessage(message, isError = false) {
    const element = document.getElementById("telegramMessage");

    if (!element) return;

    element.textContent = message;
    element.style.color = isError ? "#ff5555" : "#00cc88";
}


function updateTelegramStatus(linked) {
    const status = document.getElementById("telegramStatus");
    const button = document.getElementById("telegramLinkButton");

    if (linked) {
        status.textContent = "✅ Telegram успешно привязан к аккаунту!";
        button.textContent = "TELEGRAM ПРИВЯЗАН";
        button.disabled = true;
    } else {
        status.textContent = "❌ Telegram ещё не привязан.";
        button.textContent = "ПРИВЯЗАТЬ TELEGRAM";
        button.disabled = false;
    }
}


// TELEGRAM: получение кода

async function generateTelegramCode() {
    const button = document.getElementById("telegramLinkButton");
    const codeBox = document.getElementById("telegramCodeBox");

    button.disabled = true;
    button.textContent = "ПОЛУЧАЕМ КОД...";
    codeBox.hidden = true;

    showTelegramMessage("");

    try {
        const response = await fetch(
            `${API_URL}/api/telegram/link-code`,
            {
                method: "POST",
                credentials: "include",
                headers: {
                    "Content-Type": "application/json"
                }
            }
        );

        const result = await response.json();

        if (!response.ok) {
            throw new Error(
                result.error ||
                result.message ||
                "Не удалось получить код"
            );
        }

        if (!result.code) {
            throw new Error("Сервер не вернул код привязки");
        }

        document.getElementById("telegramCode").textContent =
            result.code;

        document.getElementById("telegramCommand").textContent =
            `/link ${result.code}`;

        codeBox.hidden = false;

        showTelegramMessage(
            "Код создан! Теперь отправь его Telegram-боту."
        );

        button.textContent = "ПОЛУЧИТЬ НОВЫЙ КОД";

    } catch (error) {
        console.error("Ошибка получения Telegram-кода:", error);

        showTelegramMessage(error.message, true);

        button.textContent = "ПОПРОБОВАТЬ СНОВА";

    } finally {
        if (button.textContent !== "TELEGRAM ПРИВЯЗАН") {
            button.disabled = false;
        }
    }
}


// Загрузка профиля

async function loadAccount() {
    try {
        const response = await fetch(`${API_URL}/api/me`, {
            credentials: "include"
        });

        if (response.status === 401 || response.status === 403) {
            window.location.href = "auth.html";
            return;
        }

        if (!response.ok) {
            throw new Error("Ошибка загрузки профиля");
        }

        const user = await response.json();

        document.getElementById("userName").textContent =
            user.full_name.toUpperCase();

        document.getElementById("username").textContent =
            user.username;

        document.getElementById("fullName").textContent =
            user.full_name;

        document.getElementById("phone").textContent =
            user.phone || "Не указан";

        document.getElementById("email").textContent =
            user.email || "Не указан";

        updateTelegramStatus(user.telegram_linked === true);

    } catch (error) {
        console.error("Ошибка загрузки профиля:", error);
        alert("Не удалось загрузить профиль");
        return;
    }

    try {
        await loadBookings();
    } catch (error) {
        console.error("Ошибка загрузки бронирований:", error);
        alert("Не удалось загрузить бронирования");
    }
}


// Кнопка привязки Telegram

document.getElementById("telegramLinkButton").addEventListener(
    "click",
    generateTelegramCode
);


// Выход из аккаунта

document.getElementById("logoutButton").addEventListener("click", async () => {
    try {
        const response = await fetch(`${API_URL}/api/logout`, {
            method: "POST",
            credentials: "include"
        });

        if (response.ok) {
            window.location.href = "auth.html";
        } else {
            alert("Не удалось выйти из аккаунта");
        }

    } catch (error) {
        console.error(error);
        alert("Ошибка соединения с сервером");
    }
});


loadAccount();