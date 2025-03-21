
# Тестирование URL Shortener

Инструкция по запуску тестов, проверки покрытия и нагрузочного тестирования.

---

## Подготовка

Убедитесь, что проект собран и контейнеры запущены:

```bash
docker-compose up --build -d
```

---

## Запуск тестов

1. Запустите тесты и сформируйте отчет
```bash
docker-compose exec web coverage run -m pytest
```

2. Скопируйте отчет из контейнера:

```bash
docker cp $(docker-compose ps -q web):/app/html_cov ./html_cov
```

Результаты можно посмотреть, открыв `html_cov/index.html`
---

## Нагрузочное тестирование

```bash
locust -f locustfile.py --host=http://localhost:8000
```

Затем откройте в браузере: http://localhost:8089
