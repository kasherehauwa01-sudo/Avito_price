# Обновление цен Google Sheets

Streamlit-приложение для автоматического обновления истории розничных цен в Google Sheets по данным из XLS/XLSX-файла.

## Назначение программы

Программа помогает поддерживать историю цен товаров в Google Таблице. Первые три колонки таблицы считаются постоянными:

| Код | Артикул | Наименование товаров |
| --- | --- | --- |

Все следующие колонки — даты в формате `дд.мм.гггг`, внутри которых хранится розничная цена товара на выбранную дату.

Приложение:

- подключается к Google Sheets;
- считывает текущую таблицу;
- создает новую колонку справа от последней даты;
- записывает выбранную дату в заголовок;
- ищет товары по артикулу;
- обновляет цену из Excel;
- добавляет отсутствующие товары в конец таблицы;
- подсвечивает желтым ячейки, где цена отличается от предыдущей даты;
- показывает подробные логи и итоговую статистику.

## Структура проекта

```text
project/
├── app.py              # Streamlit-интерфейс
├── sheets.py           # Подключение к Google Sheets и импорт цен
├── excel.py            # Чтение и нормализация Excel-файлов
├── formatter.py        # Вспомогательное форматирование A1-диапазонов
├── logger.py           # Логирование в консоль и интерфейс
├── config.py           # Константы приложения
├── credentials.json    # Ключ Service Account, не хранить в Git
├── requirements.txt    # Зависимости Python
└── README.md           # Документация
```

## Требования

- Python 3.12+
- Streamlit
- pandas
- openpyxl
- gspread
- google-auth
- google-api-python-client
- xlrd для чтения старого формата `.xls`

## Установка

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Для Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Запуск

```bash
streamlit run app.py
```

После запуска откройте адрес, который покажет Streamlit, обычно `http://localhost:8501`.

## Как пользоваться

1. Скачайте Excel-файл с актуальными ценами.
2. Откройте приложение Streamlit.
3. Выберите файл `.xls` или `.xlsx`.
4. Проверьте дату в Date Picker. По умолчанию используется сегодняшняя дата.
5. Нажмите **Загрузить XLS**.
6. Дождитесь окончания обработки.
7. Проверьте логи и итоговую статистику.

## Формат входного Excel-файла

В Excel должны быть колонки:

| Колонка Excel | Назначение в Google Sheets |
| --- | --- |
| Код | Код |
| Артикул | Артикул, главный ключ поиска |
| Наименование товаров | Наименование товаров |
| Розничная | Цена в новой колонке с датой |

Артикулы сравниваются как строки: пробелы по краям удаляются, регистр не меняется.

Если цена отсутствует, ячейка в новой колонке остается пустой. Приложение не записывает `0`, `None` или `NaN` вместо пустого значения.

## Как подключить Google Sheets через Service Account

1. Откройте [Google Cloud Console](https://console.cloud.google.com/).
2. Создайте новый проект или выберите существующий.
3. Откройте **APIs & Services → Library**.
4. Включите API:
   - Google Sheets API;
   - Google Drive API.
5. Откройте **IAM & Admin → Service Accounts**.
6. Создайте Service Account.
7. Откройте созданный аккаунт, перейдите на вкладку **Keys**.
8. Нажмите **Add key → Create new key → JSON**.
9. Скачайте файл ключа.
10. Переименуйте файл в `credentials.json`.
11. Положите `credentials.json` рядом с `app.py`.
12. Откройте нужную Google Таблицу.
13. Нажмите **Поделиться**.
14. Добавьте email сервисного аккаунта как редактора.
15. Запустите приложение.

> Важно: не публикуйте `credentials.json` в GitHub и не передавайте его третьим лицам.

## Настройка для Streamlit Cloud

На Streamlit Cloud удобнее не загружать `credentials.json`, а использовать secrets.

В настройках приложения добавьте секрет `gcp_service_account` с содержимым JSON-ключа:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "service-account@project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
universe_domain = "googleapis.com"
```

## Возможные ошибки

### Не найден credentials.json

Причина: приложение не нашло локальный файл ключа и не нашло `st.secrets['gcp_service_account']`.

Решение: положите `credentials.json` рядом с приложением или настройте Streamlit secrets.

### Permission denied или 403

Причина: сервисный аккаунт не имеет доступа к таблице или API не включены.

Решение:

- проверьте, что Google Sheets API и Google Drive API включены;
- добавьте email сервисного аккаунта в доступ к таблице с правами редактора.

### В Excel отсутствуют обязательные колонки

Причина: названия колонок отличаются от ожидаемых.

Решение: переименуйте колонки в Excel: `Код`, `Артикул`, `Наименование товаров`, `Розничная`.

### Старый `.xls` не читается

Причина: не установлена библиотека `xlrd`.

Решение: установите зависимости из `requirements.txt`.

## Альтернатива: подключение через Google Apps Script

Apps Script может быть удобен, если нельзя использовать Service Account или нужно быстро дать доступ от имени владельца таблицы. Service Account лучше подходит для серверного и промышленного сценария, где нужен отдельный технический пользователь и предсказуемые права доступа.

### Готовый пример Apps Script

```javascript
const SPREADSHEET_ID = '1s7D7d8alvIpQq2rLBGKR6RT2DJKhNPCd5VPjIhDb5Zg';
const SHEET_GID = 77890434;

function getSheet_() {
  const spreadsheet = SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheets = spreadsheet.getSheets();
  for (let i = 0; i < sheets.length; i++) {
    if (sheets[i].getSheetId() === SHEET_GID) {
      return sheets[i];
    }
  }
  throw new Error('Лист с указанным gid не найден');
}

function checkConnection() {
  const sheet = getSheet_();
  return {
    ok: true,
    spreadsheetId: SPREADSHEET_ID,
    sheetName: sheet.getName(),
    rows: sheet.getLastRow(),
    columns: sheet.getLastColumn()
  };
}

function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify(checkConnection()))
    .setMimeType(ContentService.MimeType.JSON);
}

function doPost(e) {
  try {
    const payload = JSON.parse(e.postData.contents || '{}');
    const sheet = getSheet_();

    if (payload.action === 'appendRows') {
      const rows = payload.rows || [];
      if (rows.length > 0) {
        sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
      }
      return jsonResponse_({ ok: true, appended: rows.length });
    }

    if (payload.action === 'updateCells') {
      const updates = payload.updates || [];
      updates.forEach(function(item) {
        sheet.getRange(item.range).setValue(item.value);
      });
      return jsonResponse_({ ok: true, updated: updates.length });
    }

    return jsonResponse_({ ok: false, error: 'Неизвестное действие' });
  } catch (error) {
    return jsonResponse_({ ok: false, error: String(error) });
  }
}

function jsonResponse_(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}
```

### Как открыть редактор Apps Script

1. Откройте Google Таблицу.
2. В меню выберите **Расширения → Apps Script**.
3. Удалите стартовый код из файла `Code.gs`.
4. Вставьте пример скрипта выше.
5. Сохраните проект.

### Первый запуск и разрешения

1. В выпадающем списке функций выберите `checkConnection`.
2. Нажмите **Run**.
3. Google попросит авторизацию.
4. Выберите аккаунт владельца таблицы.
5. Разрешите доступ к таблицам.
6. Убедитесь, что функция вернула объект с `ok: true`.

### Публикация веб-приложения

1. Нажмите **Deploy → New deployment**.
2. Выберите тип **Web app**.
3. В поле **Execute as** выберите себя.
4. В поле **Who has access** выберите подходящий уровень доступа.
5. Нажмите **Deploy**.
6. Скопируйте **Web app URL**.
7. Этот URL можно использовать из Streamlit для обмена данными через HTTP вместо Service Account.

### Когда лучше Apps Script

Apps Script удобен, если:

- таблицей управляет один пользователь;
- нет возможности создать Service Account;
- нужен простой HTTP-шлюз;
- важно выполнять действия от имени владельца таблицы.

### Когда лучше Service Account

Service Account лучше, если:

- приложение разворачивается как серверный сервис;
- нужен отдельный технический пользователь;
- требуется контролируемая интеграция с Google API;
- важна прозрачная настройка прав и переносимость между окружениями.
