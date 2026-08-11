import { Page, Locator } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly usernameInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly logOutButton: Locator;
  readonly successMessage: Locator;

  constructor(page: Page) {
    this.page = page;
    this.usernameInput = page.locator('#username');
    this.passwordInput = page.locator('#password');
    this.submitButton = page.locator('#submit');
    this.errorMessage = page.locator('#error');
    this.logOutButton = page.getByRole('link', { name: 'Log out' });
    this.successMessage = page.getByText('successfully logged in');
  }

  async navigate(): Promise<void> {
    try {
      await this.page.goto('https://practicetestautomation.com/practice-test-login/', {
        waitUntil: 'domcontentloaded',
      });
    } catch (error) {
      throw new Error(`Navigation to login page failed: ${(error as Error).message}`);
    }
  }

  async login(username: string, password: string): Promise<void> {
    try {
      await this.usernameInput.fill(username);
      await this.passwordInput.fill(password);
      await this.submitButton.click();
    } catch (error) {
      throw new Error(`Login action failed: ${(error as Error).message}`);
    }
  }

  async getErrorMessage(): Promise<string> {
    try {
      await this.errorMessage.waitFor({ state: 'visible', timeout: 5000 });
      return (await this.errorMessage.textContent()) || '';
    } catch (error) {
      throw new Error(`Failed to retrieve error message: ${(error as Error).message}`);
    }
  }

  async isErrorDisplayed(): Promise<boolean> {
    try {
      return await this.errorMessage.isVisible();
    } catch {
      return false;
    }
  }

  async isLogOutVisible(): Promise<boolean> {
    try {
      await this.logOutButton.waitFor({ state: 'visible', timeout: 5000 });
      return await this.logOutButton.isVisible();
    } catch {
      return false;
    }
  }

  async isSuccessMessageVisible(): Promise<boolean> {
    try {
      await this.successMessage.waitFor({ state: 'visible', timeout: 5000 });
      return await this.successMessage.isVisible();
    } catch {
      return false;
    }
  }

  async getCurrentUrl(): Promise<string> {
    try {
      return this.page.url();
    } catch (error) {
      throw new Error(`Failed to retrieve current URL: ${(error as Error).message}`);
    }
  }

  async isUsernameInputVisible(): Promise<boolean> {
    try {
      return await this.usernameInput.isVisible();
    } catch {
      return false;
    }
  }

  async isPasswordInputVisible(): Promise<boolean> {
    try {
      return await this.passwordInput.isVisible();
    } catch {
      return false;
    }
  }

  async isSubmitButtonVisible(): Promise<boolean> {
    try {
      return await this.submitButton.isVisible();
    } catch {
      return false;
    }
  }
}
