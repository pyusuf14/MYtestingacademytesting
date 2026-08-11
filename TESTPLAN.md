# Playwright Login Automation Framework — Test Plan

## Target
**URL:** `https://practicetestautomation.com/practice-test-login/`

## Credentials
- **Valid:** `student` / `Password123`
- **Post-Login URL pattern:** `practicetestautomation.com/logged-in-successfully/`

## DOM Locators
| Element        | Selector                       |
|---------------|--------------------------------|
| Username input | `#username`                   |
| Password input | `#password`                   |
| Submit button  | `#submit`                     |
| Error message  | `#error`                      |
| Logout link    | `role=link[name='Log out']`   |
| Success text   | `text=successfully logged in` |

## Architecture
```
pLAYWRIGHTTEMPLATE/
├── package.json
├── tsconfig.json
├── playwright.config.ts
├── pages/
│   └── LoginPage.ts          — POM with constructor-initialized locators
└── tests/
    ├── login-valid.spec.ts   — Positive login tests
    └── login-invalid.spec.ts — Negative login tests
```

## LoginPage.ts — Page Object Model

### Locators (constructor-initialized)
`usernameInput`, `passwordInput`, `submitButton`, `errorMessage`, `logOutButton`, `successMessage`

### Methods
| Method                    | Description                              | Exception Handling |
|--------------------------|------------------------------------------|--------------------|
| `navigate()`             | Got to login page, `domcontentloaded`    | Wrapped try/catch  |
| `login(user, pass)`      | Fill inputs + click submit               | Wrapped try/catch  |
| `getErrorMessage()`      | Wait for `#error`, return textContent    | Wrapped try/catch  |
| `isErrorDisplayed()`     | Boolean visibility check                 | Returns false on error |
| `isLogOutVisible()`      | Boolean with 5s wait                     | Returns false on error |
| `isSuccessMessageVisible()` | Boolean with 5s wait                  | Returns false on error |
| `getCurrentUrl()`        | Return `page.url()`                      | Wrapped try/catch  |
| `isUsernameInputVisible()` | Boolean visibility check              | Returns false on error |
| `isPasswordInputVisible()` | Boolean visibility check              | Returns false on error |
| `isSubmitButtonVisible()`  | Boolean visibility check              | Returns false on error |

## Test Cases

### TC-POS-01 — Successful Login (login-valid.spec.ts)
| Step | Action                      | Expected Result                          |
|------|-----------------------------|------------------------------------------|
| 1    | Navigate to login page      | Username, password, submit all visible   |
| 2    | Login: `student` / `Password123` | Form submits                        |
| 3    | Assert URL                  | Contains `logged-in-successfully`        |
| 4    | Assert success message      | Visible                                 |
| 5    | Assert Log out link         | Visible                                 |

### TC-NEG-01 — Invalid Username (login-invalid.spec.ts)
| Step | Action                      | Expected Result                          |
|------|-----------------------------|------------------------------------------|
| 1    | Navigate to login page      | Page loads                              |
| 2    | Login: `incorrectUser` / `Password123` | Form submits                    |
| 3    | Assert error visible        | `#error` displayed                      |
| 4    | Assert error text           | Contains `Your username is invalid!`     |

### TC-NEG-02 — Invalid Password (login-invalid.spec.ts)
| Step | Action                      | Expected Result                          |
|------|-----------------------------|------------------------------------------|
| 1    | Navigate to login page      | Page loads                              |
| 2    | Login: `student` / `incorrectPassword` | Form submits                  |
| 3    | Assert error visible        | `#error` displayed                      |
| 4    | Assert error text           | Contains `Your password is invalid!`     |

### TC-NEG-03 — Empty Credentials (login-invalid.spec.ts)
| Step | Action                      | Expected Result                          |
|------|-----------------------------|------------------------------------------|
| 1    | Navigate to login page      | Page loads                              |
| 2    | Login: `` (empty) / `` (empty) | Form submits                         |
| 3    | Assert error visible        | `#error` displayed                      |
| 4    | Assert error text length    | Greater than 0                          |

### TC-NEG-04 — Empty Username (login-invalid.spec.ts)
| Step | Action                      | Expected Result                          |
|------|-----------------------------|------------------------------------------|
| 1    | Navigate to login page      | Page loads                              |
| 2    | Login: `` (empty) / `Password123` | Form submits                      |
| 3    | Assert error visible        | `#error` displayed                      |
| 4    | Assert error text           | Contains `Your username is invalid!`     |

### TC-NEG-05 — Empty Password (login-invalid.spec.ts)
| Step | Action                      | Expected Result                          |
|------|-----------------------------|------------------------------------------|
| 1    | Navigate to login page      | Page loads                              |
| 2    | Login: `student` / `` (empty) | Form submits                          |
| 3    | Assert error visible        | `#error` displayed                      |
| 4    | Assert error text           | Contains `Your password is invalid!`     |

## Playwright Config
- **Browser:** Chromium only
- **Mode:** Headless
- **Workers:** 2 parallel
- **Timeout:** 30s per test
- **Retries:** 1
- **Reporters:** list + html
- **Artifacts:** screenshot + video + trace on failure
- **Viewport:** 1280×720

## Exception Handling Strategy
- Every POM method wraps Playwright operations in `try/catch`
- Descriptive error messages include original error message
- Test scripts wrap entire test body in `try/catch` with `throw new Error(...)`
- Locator visibility helpers return `false` instead of throwing on failure
- Error message retrieval uses `waitFor` with explicit timeout

## Execution Commands
```bash
npm install
npx playwright install chromium
npx playwright test                    # headless
npx playwright test --headed           # visual
npx playwright show-report             # open HTML report
```

## Results (last run)
```
6 passed (16.2s)
TC-POS-01  ✓  Successful login ... (8.5s)
TC-NEG-01  ✓  Invalid username ... (6.6s)
TC-NEG-02  ✓  Invalid password ... (2.8s)
TC-NEG-03  ✓  Empty credentials ... (1.4s)
TC-NEG-04  ✓  Empty username ... (2.0s)
TC-NEG-05  ✓  Empty password ... (2.0s)
```
