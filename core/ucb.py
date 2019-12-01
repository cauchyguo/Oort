import math
import numpy as np2

class UCB(object):

    def __init__(self):
        self.totalArms = {}
        self.totalTries = 0
        self.alpha = 0.8
        np2.random.seed(123)

    def registerArm(self, armId, reward):
        # Initiate the score for arms. [score, # of tries]
        if armId not in self.totalArms:
            self.totalArms[armId] = [reward, 1, 0]

    def registerReward(self, armId, reward):
        self.totalArms[armId][0] = reward * self.alpha + self.totalArms[armId][0] * (1.0 - self.alpha)
        self.totalArms[armId][1] += 1

    def getTopK(self, numOfSamples):
        self.totalTries += 1
        # normalize the score of all arms: Avg + Confidence
        scores = []

        for key in self.totalArms.keys():
            sc = self.totalArms[key][0]# + \
                        #math.sqrt(0.1*math.log(self.totalTries)/float(self.totalArms[key][1]))

            self.totalArms[key][2] = sc
            scores.append(sc)

        # static UCB
        index = np2.array(scores).argsort()[-numOfSamples:][::-1] + 1
        #scores = np2.array(scores)/float(sum(scores))
        #index = np2.random.choice([i for i in range(1, len(scores) + 1)], size=numOfSamples, p = scores.ravel(), replace=False)

        return index

    def getAllMetrics(self):
        return self.totalArms
