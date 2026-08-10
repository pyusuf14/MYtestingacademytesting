import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Invalid Login Scenarios', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
  });

  test('Login with incorrect username displays username invalid error', async ({ page }) => {
    try {
      await loginPage.navigate();
      await loginPage.login('incorrectUser', 'Password123');

      const isError = await loginPage.isErrorDisplayed();
      expect(isError).toBeTruthy();

      const errorText = await loginPage.getErrorMessage();
      expect(errorText).toContain('Your username is invalid!');
    } catch (error) {
      throw new Error(`Invalid username test failed: ${(error as Error).message}`);
    }
  });

  test('Login with incorrect password displays password invalid error', async ({ page }) => {
    try {
      await loginPage.navigate();
      await loginPage.login('student', 'incorrectPassword');

      const isError = await loginPage.isErrorDisplayed();
      expect(isError).toBeTruthy();

      const errorText = await loginPage.getErrorMessage();
      expect(errorText).toContain('Your password is invalid!');
    } catch (error) {
      throw new Error(`Invalid password test failed: ${(error as Error).message}`);
    }
  });

  test('Login with empty credentials displays error message', async ({ page }) => {
    try {
      await loginPage.navigate();
      await loginPage.login('', '');

      const isError = await loginPage.isErrorDisplayed();
      expect(isError).toBeTruthy();

      const errorText = await loginPage.getErrorMessage();
      expect(errorText.length).toBeGreaterThan(0);
    } catch (error) {
      throw new Error(`Empty credentials test failed: ${(error as Error).message}`);
    }
  });

  test('Login with empty username and valid password displays error', async ({ page }) => {
    try {
      await loginPage.navigate();
      await loginPage.login('', 'Password123');

      const isError = await loginPage.isErrorDisplayed();
      expect(isError).toBeTruthy();

      const errorText = await loginPage.getErrorMessage();
      expect(errorText).toContain('Your username is invalid!');
    } catch (error) {
      throw new Error(`Empty username test failed: ${(error as Error).message}`);
    }
  });

  test('Login with valid username and empty password displays error', async ({ page }) => {
    try {
      await loginPage.navigate();
      await loginPage.login('student', '');

      const isError = await loginPage.isErrorDisplayed();
      expect(isError).toBeTruthy();

      const errorText = await loginPage.getErrorMessage();
      expect(errorText).toContain('Your password is invalid!');
    } catch (error) {
      throw new Error(`Empty password test failed: ${(error as Error).message}`);
    }
  });

  test.afterEach(async ({ page }) => {
    await page.close();
  });
});
