# Imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import csv
from datetime import datetime
import time as time_module

def clean_text(text):
    replacements = {
        'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
        'á': 'a', 'à': 'a', 'â': 'a', 'ã': 'a',
        'ñ': 'n', 'í': 'i', 'ì': 'i', 'î': 'i',
        'ó': 'o', 'ò': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'ù': 'u', 'û': 'u', 'ý': 'y',
        'ü': 'u', 'ö': 'o', 'ä': 'a'
    }
    for special, english in replacements.items():
        text = text.replace(special, english)
    return text

# ... (keep imports and clean_text function the same)

def main():
    driver = None
    try:
        # Setup WebDriver
        service = Service(r"C:\Users\egeme\Desktop\chromedriver-win64\chromedriver.exe")
        driver = webdriver.Chrome(service=service)
        driver.get('https://tracker.ftgames.com/?idx=slp70xzc')
        
        time_module.sleep(5)
        
        output_filename = f'match_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        with open(output_filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['Match_Status', 'Team1', 'Team2', 'Score', 'Goals']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            processed_matches = set()
            total_matches_processed = 0
            load_more_exists = True
            
            while load_more_exists:
                # Scroll to bottom slowly
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time_module.sleep(3)
                
                # Get current matches
                matches = driver.find_elements(By.CSS_SELECTOR, '.bg-card.relative.m-2.rounded-md')
                current_batch_processed = 0

                for match in matches:
                    try:
                        teams = match.find_elements(By.CSS_SELECTOR, 'p[class*="text-2xl truncate"]')
                        score = match.find_element(By.CSS_SELECTOR, 'h1[class*="text-lg"]').text
                        match_id = f"{teams[0].text}-{teams[1].text}-{score}"
                        
                        if match_id in processed_matches:
                            continue
                            
                        processed_matches.add(match_id)
                        current_batch_processed += 1
                        total_matches_processed += 1
                        
                        status = clean_text(match.find_element(By.CSS_SELECTOR, '.grid.grid-cols-3 p.text-center').text)
                        team1 = clean_text(teams[0].text)
                        team2 = clean_text(teams[1].text)
                        
                        is_home = team1 == "EGEMENPROJETAKIMI"
                        goals_list = []
                        goals_container = match.find_element(By.CSS_SELECTOR, '.mt-1.grid.grid-cols-2')
                        
                        if is_home:
                            goal_elements = goals_container.find_elements(By.CSS_SELECTOR, '.flex.flex-col.items-end .leading-5.my-1')
                        else:
                            goal_elements = goals_container.find_elements(By.CSS_SELECTOR, '.flex.flex-col.items-start .leading-5.my-1')

                        for goal in goal_elements:
                            goal_text = clean_text(goal.text.strip())
                            if goal_text:
                                goal_parts = goal_text.split('\n')
                                if len(goal_parts) >= 2:
                                    goal_time = goal_parts[0]
                                    scorer = goal_parts[1]
                                    goals_list.append(f"{goal_time} {scorer}")
                        
                        goals_combined = " | ".join(goals_list)

                        writer.writerow({
                            'Match_Status': status,
                            'Team1': team1,
                            'Team2': team2,
                            'Score': score,
                            'Goals': goals_combined
                        })
                        print(f"Recorded match {total_matches_processed}: {team1} vs {team2} ({score})")

                    except Exception as e:
                        print(f"Error processing match: {str(e)}")
                        continue

                print(f"Total matches processed so far: {total_matches_processed}")

                # Look for Load More button
                try:
                    # Scroll to bottom again before looking for the button
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time_module.sleep(2)

                    # Try multiple methods to find the Load More button
                    load_more = None
                    try:
                        load_more = driver.find_element(By.XPATH, "//button[text()='Load more']")
                    except:
                        try:
                            load_more = driver.find_element(By.CSS_SELECTOR, "button.font-HEAD:last-of-type")
                        except:
                            buttons = driver.find_elements(By.TAG_NAME, "button")
                            load_more_buttons = [b for b in buttons if "Load more" in b.text]
                            if load_more_buttons:
                                load_more = load_more_buttons[0]

                    if load_more and load_more.is_displayed():
                        # Ensure button is clickable
                        driver.execute_script("arguments[0].scrollIntoView(true);", load_more)
                        time_module.sleep(2)

                        # Try different click methods
                        try:
                            load_more.click()
                        except:
                            try:
                                driver.execute_script("arguments[0].click();", load_more)
                            except:
                                ActionChains(driver).move_to_element(load_more).click().perform()

                        print("Clicked Load More button")
                        time_module.sleep(7)  # Wait for new content to load
                    else:
                        print("Load More button not found or not visible")
                        load_more_exists = False
                        
                except Exception as e:
                    print(f"Failed to find or click Load More button: {str(e)}")
                    load_more_exists = False

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        if driver:
            driver.quit()
        print(f"Scraping completed. Total matches processed: {total_matches_processed}")

if __name__ == "__main__":
    main()
