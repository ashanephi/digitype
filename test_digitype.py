import pytest
from digitype import DigiType

@pytest.fixture
def app():
    app = DigiType()
    app.current_user = 1  # Mock current user ID
    app.create_login_page()  # This initializes the login page to set up necessary widgets
    return app

def test_load_sound(app):
    sound = app.load_sound("key_press.mp3")
    assert sound is not None, "Sound should be loaded if the file exists"

def test_create_account(app):
    app.create_account_page()  # This initializes the account creation page
    app.new_username_entry.insert(0, "testuser")
    app.new_password_entry.insert(0, "password")
    app.email_entry.insert(0, "test@example.com")
    app.create_account()
    app.db_cursor.execute('SELECT * FROM users WHERE username=?', ("testuser",))
    user = app.db_cursor.fetchone()
    assert user is not None, "User should be created in the database"

def test_login(app):
    app.username_entry.insert(0, "testuser")
    app.password_entry.insert(0, "password")
    app.login()
    assert app.current_user == 1, "User should be logged in with correct credentials"

def test_save_progress(app):
    app.save_progress(50, 90.0)
    app.db_cursor.execute('SELECT * FROM progress WHERE user_id=? ORDER BY date DESC', (app.current_user,))
    progress = app.db_cursor.fetchone()
    assert progress is not None, "Progress should be saved in the database"

def test_check_achievements(app):
    app.check_achievements(100, 95.0)
    assert app.achievements[1]["achieved"], "Speed Demon achievement should be achieved"
    assert app.achievements[2]["achieved"], "Accuracy Master achievement should be achieved"

def test_update_profile(app):
    app.save_profile("newuser", "newpassword", "new@example.com")
    app.db_cursor.execute('SELECT * FROM users WHERE id=?', (app.current_user,))
    user = app.db_cursor.fetchone()
    assert user is not None, "User should exist in the database"
    assert user[1] == "newuser", "Username should be updated"
    assert user[2] == "newpassword", "Password should be updated"
    assert user[3] == "new@example.com", "Email should be updated"

if __name__ == "__main__":
    pytest.main(["-v", "test_digitype.py"])