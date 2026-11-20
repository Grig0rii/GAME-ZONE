const API_URL = "http://89.127.206.24:5000";

const form = document.getElementById("bookingForm");
const placeSelect = document.getElementById("place");
const message = document.getElementById("message");
const submitButton = form.querySelector("button");

// Устанавливаем минимальную дату — сегодня
const today = new Date();
const localDate = [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0")
].join("-");

document.getElementById("date").min = localDate;


// Проверяем авторизацию
async function checkAuth() {
    try {
        const response = await fetch(`${API_URL}/api/me`, {
            credentials: "include"
        });

        if (!response.ok) {
            window.location.href = "auth.html";
            return false;
        }

        return true;

    } catch (error) {
        message.textContent = "Ошибка соединения с сервером";
        message.className = "error";
        return false;
    }
}


// Загружаем игровые места
async function loadPlaces() {
    try {
        const response = await fetch(`${API_URL}/api/places`);

        if (!response.ok) {
            throw new Error("Не удалось загрузить игровые места");
        }

        const places = await response.json();

        placeSelect.innerHTML = "";

        if (places.length === 0) {
            placeSelect.innerHTML =
                '<option value="">Нет доступных мест</option>';
            return;
        }

        placeSelect.innerHTML =
            '<option value="">Выбери игровое место</option>';

        places.forEach(place => {
            const option = document.createElement("option");

            option.value = place.id;
            option.textContent = `${place.name} — ${place.type}`;

            placeSelect.appendChild(option);
        });

    } catch (error) {
        placeSelect.innerHTML =
            '<option value="">Ошибка загрузки мест</option>';

        message.textContent = error.message;
        message.className = "error";
    }
}


// Отправляем бронирование
form.addEventListener("submit", async (event) => {
    event.preventDefault();

    message.textContent = "";
    message.className = "";

    const bookingData = {
        place_id: placeSelect.value,
        date: document.getElementById("date").value,
        start_time: document.getElementById("startTime").value,
        end_time: document.getElementById("endTime").value
    };

    if (bookingData.end_time <= bookingData.start_time) {
        message.textContent =
            "Время окончания должно быть позже начала";

        message.className = "error";
        return;
    }

    submitButton.disabled = true;
    submitButton.textContent = "ОТПРАВКА...";

    try {
        const response = await fetch(`${API_URL}/api/bookings`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(bookingData)
        });

        const result = await response.json();

        if (response.status === 401) {
            window.location.href = "auth.html";
            return;
        }

        if (!response.ok) {
            throw new Error(result.error || "Ошибка бронирования");
        }

        message.textContent =
            "✓ " + result.message;

        message.className = "success";

        form.reset();

    } catch (error) {
        message.textContent = error.message;
        message.className = "error";

    } finally {
        submitButton.disabled = false;
        submitButton.textContent = "ЗАБРОНИРОВАТЬ";
    }
});


// Запускаем страницу
async function init() {
    const authorized = await checkAuth();

    if (authorized) {
        await loadPlaces();
    }
}

init();