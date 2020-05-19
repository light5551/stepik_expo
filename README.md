# stepik_expo

## Запуск

```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
python3 expo.py -i <course_id> -c <client_id> -s <client_secret>
```

## Как получить _cliend_id_ и _client_secret_

1. Зарегистрировать приложение на stepik [здесь](https://stepik.org/oauth2/applications/)
2. В поле `Client type` указать `confidential`, а в поле `Authorization grant type` указать `client-credentials` 

## Флаги

1. `-f` - чтение из файла айди курсов(пример `ids.txt`); нужно убрать флаг `-i`
2. `-v` - отключение видео
3. `-m` - кастомный формат степов: `<lesson>_<step>_<type>` вместо `<id>_<type>`

