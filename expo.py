# Run with Python 3
# Saves all step sources into foldered structure
import argparse
import os
import json
import urllib
import requests
import datetime
from bs4 import BeautifulSoup

# Enter parameters below:
# 1. Get your keys at https://stepik.org/oauth2/applications/
# (client type = confidential, authorization grant type = client credentials)


api_host = 'https://stepik.org'


def parse_arguments():
    parser = argparse.ArgumentParser(
        description='Stepik downloader')

    parser.add_argument('-c', '--client_id',
                        help='your client_id from https://stepik.org/oauth2/applications/',
                        required=True)

    parser.add_argument('-s', '--client_secret',
                        help='your client_secret from https://stepik.org/oauth2/applications/',
                        required=True)

    parser.add_argument('-i', '--course_id',
                        help='course id',
                        required=True)

    args = parser.parse_args()

    return args


args = parse_arguments()

# 2. Get a token
auth = requests.auth.HTTPBasicAuth(args.client_id, args.client_secret)
response = requests.post('https://stepik.org/oauth2/token/',
                         data={'grant_type': 'client_credentials'},
                         auth=auth)
token = response.json().get('access_token', None)
if not token:
    print('Unable to authorize with provided credentials')
    exit(1)


# 3. Call API (https://stepik.org/api/docs/) using this token.
def fetch_object(obj_class, obj_id):
    api_url = '{}/api/{}s/{}'.format(api_host, obj_class, obj_id)
    response = requests.get(api_url,
                            headers={'Authorization': 'Bearer ' + token}).json()
    return response['{}s'.format(obj_class)][0]


def fetch_objects(obj_class, obj_ids):
    objs = []
    # Fetch objects by 30 items,
    # so we won't bump into HTTP request length limits
    step_size = 30
    for i in range(0, len(obj_ids), step_size):
        obj_ids_slice = obj_ids[i:i + step_size]
        api_url = '{}/api/{}s?{}'.format(api_host, obj_class,
                                         '&'.join('ids[]={}'.format(obj_id)
                                                  for obj_id in obj_ids_slice))
        response = requests.get(api_url,
                                headers={'Authorization': 'Bearer ' + token}
                                ).json()
        objs += response['{}s'.format(obj_class)]
    return objs


def intro(course):
    summary = course['summary']
    main_picture = course['cover']
    target_audience = course['target_audience']
    requirements = course['requirements']
    description = course['description']
    video_url = None
    if course['intro_video']:
        video_url = course['intro_video']['urls'][0]['url']
    text = "Summary\n{}\nAudience\n{}\nRequirements\n{}\nDescription\n{}\n".format(summary, target_audience,
                                                                                   requirements, description)
    return text, video_url, main_picture


def main():
    course = fetch_object('course', args.course_id)
    sections = fetch_objects('section', course['sections'])
    was_intro = False

    list_of_lessons = []
    lessons_stack = []
    for section in sections:

        unit_ids = section['units']
        units = fetch_objects('unit', unit_ids)

        for unit in units:
            lesson_id = unit['lesson']
            lesson = fetch_object('lesson', lesson_id)

            step_ids = lesson['steps']
            steps = fetch_objects('step', step_ids)

            for step in steps:
                ###
                video_link = None
                if step['block']['video']:
                    video_link = step['block']['video']['urls'][0]['url']
                ###
                step_source = fetch_object('step-source', step['id'])
                path = [
                    '{} {}'.format(str(course['id']).zfill(2), course['title']),
                    '{} {}'.format(str(section['position']).zfill(2), section['title']),
                    '{} {}'.format(str(unit['position']).zfill(2), lesson['title']),
                    '{}_{}.step'.format(str(step['id']), step['block']['name'])
                ]
                try:
                    os.makedirs(os.path.join(os.curdir, *path[:-1]))
                except:
                    pass
                filename = os.path.join(os.curdir, *path)
                f = open(filename, 'w')
                data = {
                    'block': step_source['block'],
                    'id': str(step['id']),
                    'time': datetime.datetime.now().isoformat()
                }
                print(filename)
                f.write(json.dumps(data))
                f.close()

                # lesson logo
                if lesson_id not in lessons_stack:
                    lessons_stack.append(lesson_id)
                    try:
                        r = requests.get('https://stepik.org/api/lessons?ids[]={}'.format(lesson_id)).json()['lessons'][0]
                        logo_id, cover_url = r['id'], r['cover_url']
                        path[-1] = '{}_logo.png'.format(logo_id)
                        filename = os.path.join(os.curdir, *path)
                        p = requests.get(cover_url)
                        with open(filename, "wb") as out:
                            out.write(p.content)
                    except:
                        pass
                ##
                # intro
                if not was_intro:
                    text, video, main_picture = intro(course)
                    try:
                        os.makedirs(os.path.join(os.curdir, path[0], 'intro'))
                    except:
                        pass
                    if video:
                        intro_video_filename = os.path.join(os.curdir, path[0], 'intro', 'intro_file.mp4')
                        urllib.request.urlretrieve(video, intro_video_filename)
                    intro_file = os.path.join(os.curdir, path[0], 'intro', 'intro_text.txt')
                    out = open(intro_file, "w")
                    out.write(text)
                    out.close()
                    if main_picture:
                        r = requests.get("https://stepik.org" + main_picture)
                        main_picture_file = os.path.join(os.curdir, path[0], 'intro', 'logo.png')
                        with open(main_picture_file, 'wb') as file:
                            file.write(r.content)
                was_intro = True

                # files
                lesson_for_file = step['lesson']
                if lesson_for_file not in list_of_lessons:
                    r = requests.get('https://stepik.org/api/attachments?lesson={}'.format(lesson_for_file),
                                     headers={'Authorization': 'Bearer ' + token}).json()
                    list_of_lessons.append(lesson_for_file)
                    attach = r['attachments']
                    for i in attach:
                        try:
                            filename_attach = i['name']
                            url_file = i['file']
                            data = requests.get('https://stepik.org' + url_file).text
                            path[-1] = filename_attach
                            filename = os.path.join(os.curdir, *path)
                            with open(filename, 'w') as f:
                                f.write(data)
                            print(filename)
                        except:
                            pass

                # video
                if video_link:
                    video_filename = "{}_{}.mp4".format(str(step['position']).zfill(2), step['block']['name'])
                    path[-1] = video_filename
                    filename = os.path.join(os.curdir, *path)
                    urllib.request.urlretrieve(video_link, filename)
                # pictures
                html = step['block']['text']
                soup = BeautifulSoup(html, 'html.parser')
                tags = soup.find_all(['img'])
                for index, tag in enumerate(tags):
                    path[-1] = '{}_{}_{}_photo.png'.format(step['id'], step['block']['name'], index)
                    filename = os.path.join(os.curdir, *path)
                    try:
                        p = requests.get(tag['src'])
                        out = open(filename, "wb")
                        out.write(p.content)
                        out.close()
                        print(filename)
                    except:
                        pass


if __name__ == '__main__':
    main()
