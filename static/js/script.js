document.addEventListener('DOMContentLoaded', function () {
  const countrySelect = document.getElementById('country');
  const giveSelect = document.getElementById('give_currency');
  const getSelect = document.getElementById('get_currency');
  const citySelect = document.getElementById('city');
  const fullnameInput = document.getElementById('fullname');
  const emailInput = document.getElementById('email');
  const datetimeInput = document.getElementById('datetime');
  const form = document.getElementById('exchangeForm');

  let countryData = null;

  // Всплывающее уведомление
  function showNotification(message) {
    const container = document.getElementById('notification-container');
    const note = document.createElement('div');
    note.className = 'notification';
    note.textContent = message;
    container.appendChild(note);
    setTimeout(() => note.remove(), 5000);
  }

  // Загрузка данных страны
  async function updateFields(country) {
    if (!country) return;
    try {
      const res = await fetch(`/api/country/${encodeURIComponent(country)}`);
      const data = await res.json();
      if (data.error) return;

      countryData = data;

      [giveSelect, getSelect, citySelect].forEach(sel => {
        sel.innerHTML = '<option value="" selected disabled>Выберите...</option>';
      });

      const allCurrencies = [...new Set([...data.currencies_from_crypto, ...data.currencies_from_fiat])];
      allCurrencies.forEach(cur => {
        const opt = document.createElement('option');
        opt.value = cur;
        opt.textContent = cur;
        giveSelect.appendChild(opt);
      });

      data.cities.forEach(city => {
        const opt = document.createElement('option');
        opt.value = city;
        opt.textContent = city;
        citySelect.appendChild(opt);
      });
    } catch (err) {
      console.error('Ошибка при загрузке данных страны:', err);
    }
  }

  // Обновление валюты "получаете"
  function updateReceiveCurrencies() {
    if (!countryData || !giveSelect.value) return;

    const cryptoSet = new Set(countryData.currencies_from_crypto);
    const fiatSet = new Set(countryData.currencies_from_fiat);

    let available = [];

    if (cryptoSet.has(giveSelect.value)) {
      available = [...fiatSet];
    } else if (fiatSet.has(giveSelect.value)) {
      available = [...cryptoSet];
    }

    getSelect.innerHTML = '<option value="" selected disabled>Выберите...</option>';
    available.forEach(cur => {
      if (cur !== giveSelect.value) {
        const opt = document.createElement('option');
        opt.value = cur;
        opt.textContent = cur;
        getSelect.appendChild(opt);
      }
    });
  }

  // Проверка email
  function validateEmail(email) {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return regex.test(email.trim());
  }

  // Проверка даты
  function validateDate() {
      const inputValue = datetimeInput.value;
      if (!inputValue) {
        showNotification("Укажите дату и время визита.");
        return false;
      }

      const inputDate = new Date(inputValue);
      const now = new Date();
      const oneYearLater = new Date();
      oneYearLater.setFullYear(now.getFullYear() + 1);

      // Проверка: валидна ли дата вообще
      if (isNaN(inputDate.getTime())) {
        showNotification("Неверный формат даты. Пожалуйста, выберите корректную дату.");
        return false;
      }

      if (inputDate <= now) {
        showNotification(`Значение должно быть ${now.toLocaleString()} или позже.`);
        return false;
      }

      if (inputDate > oneYearLater) {
        showNotification("Дата визита не может быть позже чем через год.");
        return false;
      }

      return true;
    }


  // Проверка ФИО
  function validateFullname(name) {
    const cleaned = name.trim();
    const validChars = /^[А-Яа-яЁёA-Za-z\s]+$/;
    if (!validChars.test(cleaned)) {
      showNotification("ФИО должно содержать только буквы и пробелы.");
      return false;
    }

    const words = cleaned.split(/\s+/);
    if (words.length !== 3) {
      showNotification("ФИО должно состоять из трёх слов (например: Иванов Иван Иванович).");
      return false;
    }

    return true;
  }

  // Проверка перед отправкой
  form.addEventListener('submit', e => {
    if (giveSelect.value === getSelect.value) {
      e.preventDefault();
      showNotification("Нельзя обменивать одинаковые валюты!");
      return;
    }

    if (!validateFullname(fullnameInput.value)) {
      e.preventDefault();
      return;
    }

    if (!validateEmail(emailInput.value)) {
      e.preventDefault();
      showNotification("Введите корректный email с символом '@'.");
      return;
    }

    if (!validateDate()) {
      e.preventDefault();
      return;
    }
  });

  // События
  countrySelect.addEventListener('change', e => updateFields(e.target.value));
  giveSelect.addEventListener('change', updateReceiveCurrencies);
});
