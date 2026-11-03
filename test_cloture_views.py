from app import app, db, Payment, User
from flask_login import login_user

with app.test_request_context():
    with app.test_client() as c:
        u33 = User.query.get(33)
        # Login via test client
        with c.session_transaction() as sess:
            sess['_user_id'] = str(u33.id)
            sess['_fresh'] = True
        
        # Follow redirects
        res_cloture = c.get('/users/activity/cloture?period=today', follow_redirects=True)
        cloture_html = res_cloture.get_data(as_text=True)
        print("mriliass cloture status:", res_cloture.status_code)
        print("REC-0810 in mriliass cloture?", "REC-0810" in cloture_html)
        print("REC-0813 in mriliass cloture?", "REC-0813" in cloture_html)
        print("650 in mriliass cloture?", "650" in cloture_html)

        res_act = c.get('/users/activity?period=today', follow_redirects=True)
        act_html = res_act.get_data(as_text=True)
        print("mriliass activity status:", res_act.status_code)
        print("REC-0810 in mriliass activity?", "REC-0810" in act_html)
        print("REC-0813 in mriliass activity?", "REC-0813" in act_html)
