import { test, expect } from '@playwright/test';
import { LoginPage } from '../pages/LoginPage';

test.describe('Valid Login Scenarios', () => {
  let loginPage: LoginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
  });

  test('Successful login navigates to logged-in-successfully page with logout button visible', async ({ page }) => {
    try {
      await loginPage.navigate();

      await expect(await loginPage.isUsernameInputVisible()).toBeTruthy();
      await expect(await loginPage.isPasswordInputVisible()).toBeTruthy();
      await expect(await loginPage.isSubmitButtonVisible()).toBeTruthy();

      await loginPage.login('student', 'Password123');

      const currentUrl = await loginPage.getCurrentUrl();
      expect(currentUrl).toContain('practicetestautomation.com/logged-in-successfully/');

      const successVisible = await loginPage.isSuccessMessageVisible();
      expect(successVisible).toBeTruthy();

      const logOutVisible = await loginPage.isLogOutVisible();
      expect(logOutVisible).toBeTruthy();
    } catch (error) {
      throw new Error(`Valid login test failed: ${(error as Error).message}`);
    }
  });

  test.afterEach(async ({ page }) => {
    await page.close();
  });
});
