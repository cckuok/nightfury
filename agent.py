import os
import d2v
import json
import math
import config
import shutil
import numpy as np
import logging
import browser
import traceback
import cPickle as pickle

from rlpy.Domains.Domain import Domain
from rlpy.Representations import RBF
from rlpy.Policies import eGreedy
from rlpy.Experiments import Experiment
from rlpy.Agents import LSPI_SARSA, SARSA

class NDomain(Domain):
    GOAL_REWARD = 10
    STEP_REWARD = -1
    def __init__(self, b):
        self.b = b  # Browser

        self.statespace_limits = np.array(self.b.get_state_vector_limits())
        self.continuous_dims = self.b.get_continuous_dimensions()
        self.DimNames = ['DimName'] * len(self.statespace_limits)
        self.episodeCap = 5
        self.actions_num = self.b.get_actions_num()
        self.discount_factor = 0.6

    def s0(self):
        self.b.reset(hard=True)
        self.b.navigate_to_url('http://127.0.0.1:8000')
        self.b.enhance_state_info()
        state_vector, elements = self.b.get_state_vector()
        return(state_vector, self.isTerminal(), self.possibleActions(elements=elements))

    def possibleActions(self, elements=None):
        if elements == None:
            _, elements = self.b.get_state_vector()
        return(self.b.non_none_indices(elements))

    def isTerminal(self):
        return(bool(re.findall('logout', self.b.get_current_state().text, re.IGNORECASE)))

    def step(self, a):
        state_vector, elements = self.b.get_state_vector()
        self.b.act_on(elements[a])
        new_state_vector, new_elements = self.b.get_state_vector()
        terminal = self.isTerminal()
        reward = self.GOAL_REWARD if terminal else self.STEP_REWARD
        return(reward, new_state_vector, terminal, self.possibleActions(elements=new_elements))

    def __deepcopy__(self, memo):
        return(self)


class Nightfury(object):
    def __init__(self):
        self._init_logging()
        self.browser = browser.NBrowser()

    def _init_logging(self):
        logger = logging.getLogger()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)8s] --- %(message)s (%(filename)s:%(lineno)s)",
            "%H:%M")
        logger.setLevel(logging.DEBUG)

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        logger.addHandler(handler)

        file_handler = logging.FileHandler('/tmp/nightfury.log')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)

    def make_experiment(self, exp_id=1, path="results/"):
        opt = {}
        opt["exp_id"] = exp_id
        opt["path"] = path

        domain = NDomain(self.browser)
        opt["domain"] = domain

        representation = RBF(opt["domain"], num_rbfs=int(206,))
        policy = eGreedy(representation, epsilon=0.3)

        agent = SARSA(
            representation=representation,
            policy=policy,
            discount_factor=domain.discount_factor,
            initial_learn_rate=0.1,
            learn_rate_decay_mode="boyan",
            boyan_N0=100,
            lambda_=0.4
        )
        opt["agent"] = agent

        opt["checks_per_policy"] = 10
        opt["max_steps"] = 5000
        opt["num_policy_checks"] = 10
        experiment = Experiment(**opt)
        return(experiment)

    def run(self):
        exp = self.make_experiment()
        exp.run(visualize_steps=False)

    def close(self):
        if self.browser: self.browser.close()


if __name__ == "__main__":
    # agent = NAgent()
    # print(agent.w2v('profile'))
    try:
        nf = None
        nf = Nightfury()
        nf.run()
    except KeyboardInterrupt:
        pass
    except Exception, e:
        print(traceback.print_exc())
    finally:
        if nf:
            nf.close()
