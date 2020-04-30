import flask
import run
import users
import emails

def send_digest():
    for user in users.all_users():
        try:
            if user.is_active and user.data.get('digest_allowed'):
                digest = flask.render_template('email/digest.md', user=user)
                print('Sending to user %s' % (user.get_id(),))
                user.send_email(digest)
        except Exception as e:
            print('Error:', e)




if __name__ == '__main__':
    with run.app.app_context():
        print('Sending digest')
        send_digest()

