let selectedCity = null;
let refreshInterval = null;
document.getElementById("searchBtn").addEventListener("click", searchCity);
async function searchCity() {
    showLoading();
    this.style.padding = "9px 14px";
    setTimeout(()=>{
        this.style.padding = "10px 15px";
    },50)
    const query = document.getElementById("cityInput").value.trim();
    if (!query) return;

    const res = await fetch(`/api/search-city/?q=${encodeURIComponent(query)}`);
    const data = await res.json();

    const resultsDiv = document.getElementById("results");
    resultsDiv.innerHTML = "";

    if (!data.results || data.results.length === 0) {
        resultsDiv.innerHTML = "<p style='margin: 20px;'>Aucun résultat</p><p style='margin: 20px; color: rgb(167, 18, 18);'>Le nom de la ville est peut être incorrecte ou une erreur de connexion</p>";
        hideLoading();
        return;
    }
        data.results.forEach(city => {
        const div = document.createElement("div");
        div.textContent = `${city.name}${city.state ? ", " + city.state : ""}, ${city.country}`;
        div.addEventListener("click", () => selectCity(city));
        resultsDiv.appendChild(div);
    });
    hideLoading();
    }

function selectCity(city) {
    selectedCity = city;
    loadWeather();

    if (refreshInterval) {
        clearInterval(refreshInterval);
    }

    refreshInterval = setInterval(() => {
        if (selectedCity) {
            loadWeather();
        }
    }, 60000);
}

async function loadWeather() {
    showLoading();
    if (!selectedCity) return;

    const res = await fetch(
        `/api/weather/?lat=${selectedCity.lat}&lon=${selectedCity.lon}`
    );
    const data = await res.json();

    const weatherDiv = document.getElementById("weather");
    weatherDiv.style.display = "block";

    if (data.error) {
        weatherDiv.innerHTML = `<p>Erreur : ${data.error}</p>`;
        hideLoading();
        return;
    }

    const current = data.current;
    const forecast = data.forecast;

    let html = `
        <h2>${current.name}</h2>
        <p><strong>Température :</strong> ${current.main.temp} °C</p>
        <p><strong>Ressenti :</strong> ${current.main.feels_like} °C</p>
        <p><strong>Humidité :</strong> ${current.main.humidity} %</p>
        <p><strong>Description :</strong> ${current.weather[0].description}</p>
        <p><strong>Vent :</strong> ${current.wind.speed} m/s</p>

        <h3>Prévisions</h3>
    `;

    forecast.list.slice(0, 8).forEach(item => {
        html += `
            <div class="forecast-item">
                <p><strong>${item.dt_txt}</strong></p>
                <p>${item.main.temp} °C - ${item.weather[0].description}</p>
            </div>
        `;
    });

    weatherDiv.innerHTML = html;
    hideLoading();
    weatherDiv.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    })
}

