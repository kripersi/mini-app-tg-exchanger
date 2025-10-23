// === Telegram Mini App integration ===
const tg = window.Telegram?.WebApp;
if (tg) tg.expand(); // разворачиваем WebApp на весь экран

document.addEventListener("DOMContentLoaded", () => {
  const countrySelect = document.getElementById("country");
  const giveSelect = document.getElementById("give_currency");
  const getSelect = document.getElementById("get_currency");
  const citySelect = document.getElementById("city");

  // ======== ПРИВЕТСТВИЕ ПОЛЬЗОВАТЕЛЯ ========
  const user = tg?.initDataUnsafe?.user;
  if (user) {
    const greetingContainer = document.getElementById("greeting-container");
    if (greetingContainer) {
      greetingContainer.innerHTML = `<b>${user.first_name || user.username || "гость"}</b>`;
    }

    // автоматом заполняем скрытые поля формы
    const userIdInput = document.querySelector('input[name="user_id"]');
    const firstNameInput = document.querySelector('input[name="first_name"]');
    const lastNameInput = document.querySelector('input[name="last_name"]');
    const usernameInput = document.querySelector('input[name="username"]');

    if (userIdInput) userIdInput.value = user.id;
    if (firstNameInput) firstNameInput.value = user.first_name || "";
    if (lastNameInput) lastNameInput.value = user.last_name || "";
    if (usernameInput) usernameInput.value = user.username || "";
  }

  // ======== ОБРАБОТКА ВЫБОРА СТРАНЫ ========
  if (countrySelect) {
    countrySelect.addEventListener("change", async () => {
      const country = countrySelect.value;
      if (!country) return;

      const response = await fetch(`/api/country/${country}`);
      if (!response.ok) {
        console.error("Ошибка загрузки страны:", country);
        return;
      }

      const data = await response.json();
      updateSelects(data);
    });
  }

  // ======== ОБНОВЛЕНИЕ СПИСКОВ ВАЛЮТ И ГОРОДОВ ========
  function updateSelects(data) {
    giveSelect.innerHTML = "";
    getSelect.innerHTML = "";
    citySelect.innerHTML = "";

    const allCurrencies = [
      ...data.currencies_from_crypto,
      ...data.currencies_from_fiat,
    ];

    allCurrencies.forEach((cur) => {
      const opt1 = document.createElement("option");
      opt1.value = cur;
      opt1.textContent = cur;
      giveSelect.appendChild(opt1);

      const opt2 = document.createElement("option");
      opt2.value = cur;
      opt2.textContent = cur;
      getSelect.appendChild(opt2);
    });

    data.cities.forEach((city) => {
      const opt = document.createElement("option");
      opt.value = city;
      opt.textContent = city;
      citySelect.appendChild(opt);
    });
  }

  // ======== ЗАПРЕТ ОДИНАКОВЫХ ВАЛЮТ ========
  if (giveSelect && getSelect) {
    const validateCurrencies = () => {
      if (giveSelect.value && getSelect.value && giveSelect.value === getSelect.value) {
        showNotification("Нельзя обменивать одинаковые валюты!");
      }
    };
    giveSelect.addEventListener("change", validateCurrencies);
    getSelect.addEventListener("change", validateCurrencies);
  }

  // ======== УВЕДОМЛЕНИЯ ========
  function showNotification(message) {
    let container = document.getElementById("notification-container");
    if (!container) {
      container = document.createElement("div");
      container.id = "notification-container";
      document.body.appendChild(container);
    }

    const notif = document.createElement("div");
    notif.classList.add("notification");
    notif.textContent = message;

    container.appendChild(notif);
    setTimeout(() => notif.remove(), 3000);
  }
});
