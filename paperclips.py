
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.select import Select
from selenium.webdriver.common.action_chains import ActionChains

from time import sleep
from traceback import print_exc
from random import random
from os import getcwd

def launch_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("user-data-dir=" + getcwd() + "/profile")

    driver = webdriver.Chrome(chrome_options=options)
    driver.get("http://www.decisionproblem.com/paperclips/index2.html")
    return driver

number_words = {
    'thousand': 1e3,
    'million': 1e6,
    'billion': 1e9,
    'trillion': 1e12,
    'quadrillion': 1e15,
    'quintillion': 1e18,
    'sextillion': 1e21,
    'septillion': 1e24,
    'octillion': 1e27,
    'nonillion': 1e30,
    'decillion': 1e33,
    'undecillion': 1e36,
    'duodecillion': 1e39,
    'tredecillion': 1e42,
}

def run(driver):
    def parse_number(s):
        # expected format: "123.4 trillion ..."
        try:
            components = s.replace(',', '').split(' ')
            if not components:
                # likely an empty string
                return None
            n = float(components[0])
            w = 1
            if len(components) > 1:
                w = number_words[components[1]]
            return n * w
        except Exception:
            print_exc()
            print('caught exception parsing number, returning None')
            return None

    def nv(id):
        element = driver.find_element_by_id(id)
        if not element.is_displayed():
            return None
        try:
            return parse_number(element.text)
        except Exception:
            return None
    def click(id):
        button = driver.find_element_by_id(id)
        if button.is_displayed() and button.is_enabled():
            button.click()
            return True
        return False

    inventory_history = []
    def raise_or_lower(current_inventory):
        nonlocal inventory_history
        if current_inventory is None:
            return
        SAMPLES = 4
        inventory_history.append(current_inventory)
        inventory_history = inventory_history[-SAMPLES:]
        if len(inventory_history) < SAMPLES:
            return None
        inventory_delta = current_inventory - inventory_history[0]
        # make sure we can get out of the situation where inventory is close to 0
        if current_inventory < 0.005 * totalClips:
            return 'raise'
        if abs(inventory_delta) > 0.001 * totalClips:
            inventory_history = []
            # lower prices if inventory is increasing and above a threshold
            if inventory_delta > 0 and current_inventory > 0.01 * totalClips:
                return 'lower'
            elif inventory_delta < 0 and current_inventory < 0.1 * totalClips:
                return 'raise'

    def next_purchase(processors, memory):
        if processors is None or memory is None:
            return None
        # could add more processors earlier, e.g.
        # 2+1 3+1 3+2 3+3 .. 3+7 4+8 8+16 24+48 30+70
        if processors >= 30 and memory < 70:
            return 'memory'
        if processors < 0.5 * memory:
            return 'processors'
        return 'memory'

    tournament_cooldown = 0
    def run_tournament_periodically():
        nonlocal tournament_cooldown
        if tournament_cooldown > 0:
            tournament_cooldown -= 1
        elif click('btnNewTournament'):
            tournament_cooldown = 240
            strat = Select(driver.find_element_by_id('stratPicker'))
            strat.select_by_index(len(strat.options) - 1)
            click('btnRunTournament')

    def buy_any_upgrade():
        # probably this should be a preference order, and we might also want to idle for creativity
        enabled_project_buttons = driver.find_elements_by_css_selector('button.projectButton:enabled')
        # skip these for now
        enabled_project_buttons = [e for e in enabled_project_buttons if 'Photonic' not in e.text]
        if enabled_project_buttons:
            print('Now buying:', enabled_project_buttons[0].text)
            enabled_project_buttons[0].click()

    def least_monetary_upgrade_cost():
        projects = driver.find_elements_by_css_selector('button.projectButton')
        projects = [p for p in projects if p.is_displayed()]
        def cost(project):
            if '$' in project.text:
                _, _, rest = project.text.partition('$')
                amount = rest.split(')')[0]
                return parse_number(amount)
        costs = [cost(p) for p in projects if cost(p)]
        if costs:
            return min(costs)

    def withdraw_if_cash_enough():
        cash = nv('investmentBankroll')
        cost = least_monetary_upgrade_cost()
        if cost and cash >= cost:
            click('btnWithdraw')

    def upgrade_computer():
        np = next_purchase(nv('processors'), nv('memory'))
        if np == 'processors':
            click('btnAddProc')
        elif np == 'memory':
            click('btnAddMem')

    def center_slider():
        slider = driver.find_element_by_id('slider')
        if slider:
            w = slider.size['width'] / 2
            ac = ActionChains(driver)
            ac.move_to_element_with_offset(slider, w, 1)
            ac.click()
            ac.perform()
            
    def stage1():
        # buy wire if low
        wire = nv('wire')
        if wire < 500:
            click('btnBuyWire')
        # buy an autoclipper, if we still have enough for one wire purchase
        # this is a little too conservative early on
        funds = nv('funds')
        wire_price = nv('wireCost')
        clipper_price = nv('clipperCost')
        mega_price = nv('megaClipperCost')
        if clipper_price and funds > wire_price + clipper_price:
            # hold off on clippers when megaclippers are available
            if not mega_price or clipper_price < 0.002 * mega_price:
                click('btnMakeClipper')

        if mega_price and mega_price < 0.8 * funds:
            click('btnMakeMegaClipper')

        # pricing is hard
        rl = raise_or_lower(nv('unsoldClips'))
        if rl == 'lower':
            click('btnLowerPrice')
        elif rl == 'raise':
            click('btnRaisePrice')
        # marketing
        marketing = nv('adCost')
        if marketing < 0.5 * funds:
            click('btnExpandMarketing')

        # computing
        upgrade_computer()

        # one-time investment to trigger the $1M project
        invested = nv('portValue')
        if invested == 0:
            click('btnInvest')


        # TODO upgrade engine

        #withdraw investment
        withdraw_if_cash_enough()

        run_tournament_periodically()
        buy_any_upgrade()

    def stage2():
        buy_any_upgrade()
        upgrade_computer()
        click('btnSynchSwarm')
        click('btnEntertainSwarm')
        farms = nv('farmLevel')
        if farms == 0:
            click('btnMakeFarm')
            farms += 1
        harvesters = nv('harvesterLevelDisplay')
        if harvesters == 0:
            click('btnMakeHarvester')
            harvesters += 1
        wire_drones = nv('wireDroneLevelDisplay')
        if wire_drones == 0:
            click('btnMakeWireDrone')
            wire_drones += 1
        factories = nv('factoryLevelDisplay')
        if factories == 0:
            click('btnMakeFactory')
            factories += 1

        available_matter = nv('availableMatterDisplay')
        acquired_matter = nv('acquiredMatterDisplay')
        wire = nv('nanoWire')

        if farms and harvesters and wire_drones and factories:
            # buy things that are very cheap
            unused = nv('unusedClipsDisplay')
            farm_cost = nv('farmCost')
            if farm_cost * 1000 < unused:
                click('btnFarmx100')
            tower_cost = nv('batteryCost')
            if tower_cost * 1000 < unused:
                click('btnBatteryx100')
            harvester_cost = nv('harvesterCostDisplay')
            if harvester_cost * 10000 < unused:
                click('btnHarvesterx1000')
            wire_drone_cost = nv('wireDroneCostDisplay')
            if wire_drone_cost * 10000 < unused:
                click('btnWireDronex1000')

            energy_consumption = nv('powerConsumptionRate')
            energy_production = nv('powerProductionRate')
            if energy_consumption >= energy_production:
                click('btnMakeFarm')
            else:
                if wire > 0:
                    click('btnMakeFactory')
                else:
                    matter = nv('acquiredMatterDisplay')
                    if matter > 0:
                        click('btnMakeWireDrone')
                    else:
                        click('btnMakeHarvester')

            center_slider()
            
            run_tournament_periodically()

            if random() < 0.1:
                r = nv('clipmakerRate2')
                u = nv('unusedClipsDisplay')
                fc = nv('factoryCostDisplay')
                print('unused', u, 'rate', r, 'next factory cost', fc, 'expected in', (fc - u) / r)

        if available_matter == 0 and acquired_matter == 0 and wire == 0:
            click('btnHarvesterReboot')
            click('btnWireDroneReboot')
            click('btnFactoryReboot')

    def stage3():
        center_slider()
        buy_any_upgrade()
        upgrade_computer()
        click('btnIncreaseMaxTrust')
        click('btnIncreaseProbeTrust')
        speed = nv('probeSpeedDisplay')
        if speed == 0:
            click('btnRaiseProbeSpeed')
        exploration = nv('probeNavDisplay')
        if exploration == 0:
            click('btnRaiseProbeNav')
        factory = nv('probeFacDisplay')
        if factory == 0:
            click('btnRaiseProbeFac')
        harvester = nv('probeHarvDisplay')
        if harvester == 0:
            click('btnRaiseProbeHarv')
        wire = nv('probeWireDisplay')
        if wire == 0:
            click('btnRaiseProbeWire')

        self_rep = nv('probeRepDisplay')
        hazard = nv('probeHazDisplay')
        if hazard <= self_rep:
            click('btnRaiseProbeHaz')
        else:
            click('btnRaiseProbeRep')

        combat = nv('probeCombatDisplay')
        if combat is not None and combat < 5:
            click('btnLowerProbeHaz')
            click('btnLowerProbeRep')
            click('btnRaiseProbeCombat')
            click('btnRaiseProbeCombat')
            
        click('btnMakeProbe')
            
    while True:
        try:
            totalClips = nv('clips')
            if totalClips < 1000:
                click('btnMakePaperclip')
            #print(totalClips)
            wire = nv('wire')
            if wire is not None:
                stage1()
            elif driver.find_element_by_id('probeDesignDiv').is_displayed():
                stage3()
            else:
                stage2()
            sleep(0.5)
        except KeyboardInterrupt:
            print("caught keyboard interrupt, exiting")
            return
        except Exception as e:
            print_exc()
            print("caught other exception, continuing")
    

def main():
    driver = launch_driver()
    run(driver)

# note: game is saved in local storage after a certain interval so if this exits right away progress might not be saved

if __name__ == '__main__':
    main()

