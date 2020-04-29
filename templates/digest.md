{% set tz = user.data.timezone %}
{% if not tz %}
{% set tz = "UTC" %}
{% set tzunset = true %}
{% endif %}
{% set events = digest_events() %}
{% set news = digest_news() %}

Dear {{ user.data.fullname }},

this is your weekly digest from <https://grt-home.org>.
Your timezone is: {{ tz }}. 
{% if tzunset %}
Preferred timezone for future digests can be set at <{{ url_for('profile', _external=True) }}>.
{% endif %}

{% if events.items %}

## Seminars next week

{% for item in events.items %}

{% if item.duration and item.duration!='unknown' %}
**{{ item.date | format_datetime(site.digest.dateformat, tz) -}}
    -
    {{- item.date | modify_datetime(minutes=(item.duration | int)) | format_datetime(site.digest.dateformat2, tz) }}**
{% else %}
**{{ item.date | format_datetime(site.digest.dateformat, tz) }}**
{% endif %}

{% if item.seminar %}
**{{ item.seminar }}**
{% endif %}


{% if item.talk_speaker %}
**{{ item.talk_speaker }}**
{% endif %}


{% if item.talk_title %}
*{{ item.talk_title }}*
{% endif %}

{{ item.content|safe }}

{% endfor %}

{% endif %}

{% if news.items %}
## Latest news

{% for item in news.items %}

**{{ item.title }}**, {{ item.date | format_datetime(site.digest.dateformat, tz) }} by {{ item.username | user_fullname }}

{{ item.content|safe }}

{% endfor %}

{% endif %}


Have a nice week,

GRT at home (<https://grt-home.org>)

