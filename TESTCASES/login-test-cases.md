| Test Case ID | Description                                           | Positive Path | Negative Path | Expected Result                                  | Priority |
|--------------|-------------------------------------------------------|---------------|---------------|--------------------------------------------------|----------|
| TC_001       | Verify successful login with valid credentials        | /login/success | /login/failure | User is successfully logged in and redirected to dashboard. | High     |
| TC_002       | Attempt login with incorrect username                 | /login/incorrect_username | /login/success | Error message displayed, user remains on the login page | High     |
| TC_003       | Verify login with empty username                      | /login/empty_username | /login/success | Error message displayed, user remains on the login page | Medium   |
| TC_004       | Attempt login with invalid password                    | /login/invalid_password | /login/failure | Error message displayed, user remains on the login page | High     |
| TC_005       | Verify login with blank username and password         | /login/blank_username_password | /login/failure |  Error message displayed, user remains on the login page | Medium   |
| TC_006       | Login with invalid username and password              | /login/invalid_username_password | /login/failure | Error message displayed, user remains on the login page | High     |
| TC_007       | Verify account lockout after multiple failed attempts  | /login/failed_attempts | /login/success   | Account is locked and a notification appears.     | High     |
| TC_008       | Test with special characters in username          | /login/special_username | /login/failure |  Error message displayed, user remains on the login page | Medium   |
| TC_009       | Verify case-sensitive password input                  | /login/case_sensitive_password | /login/success | Password is validated correctly                      | High     |
| TC_010       | Test with special characters in password           | /login/special_password | /login/failure |  Error message displayed, user remains on the login page | Medium   |
| TC_011       | Attempt login with a very long username              | /login/long_username | /login/failure | Error message displayed, user remains on the login page | Low      |
| TC_012       | Verify correct redirection after successful login    | /login/success  | /dashboard   | User is redirected to the dashboard.             | High     |
| TC_013       | Test with an empty session ID                        | /login/empty_session_id | /login/success | Session is created and logged in.                  | Medium   |
| TC_014       |  Login with a password that doesn't match the username | /login/password_doesnt_match_username | /login/failure | Error message displayed, user remains on the login page | High     |
| TC_015       | Test with multiple attempts exceeding maximum limit    | /login/max_attempts | /login/failure | User is locked out after reaching the limit.           | High     |
| TC_016       | Login with a valid account and password                | /login/valid_account_password | /login/failure | User is logged in successfully                         | High     |
| TC_017       | Test with an empty session expiry time          | /login/session_expiry_time | /login/success | User is logged in with the correct session expiry.    | Medium   |
| TC_018       | Verify success with a valid account and password | /login/valid_account_password  | /login/failure | Error message displayed, user remains on the login page | High     |
| TC_019       | Test with a different session expiry time          | /login/session_expiry_time | /login/success | User is logged in with the correct session expiry.    | Medium   |
| TC_020       | Verify error message if login fails after multiple attempts | /login/failed_attempts | /login/failure | Displays appropriate error message                        | High     |
