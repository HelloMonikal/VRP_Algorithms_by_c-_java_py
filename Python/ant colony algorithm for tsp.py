# --* coding = utf-8 *--
from collections import namedtuple
from math import sqrt
from operator import attrgetter
from random import randint, random, seed
from time import time

import matplotlib.pyplot as plt
from tqdm import tqdm


def main():
    start = time()
    seed(start)
    mainProgram = AntColonyAlgorithm(filePath=r"./Data/convrp_12_test_4.vrp",  # data file's local path
                                     population=30,
                                     alpha=5,
                                     beta=5,
                                     sigma=0.8,
                                     Q=5,
                                     inition=1,
                                     iteration=10)
    mainProgram.run()
    mainProgram.display(startTime=start,
                        endTime=time())


class customerInfomation(object):
    def __init__(self, filePath):
        customer = namedtuple(
            "customer", ('name', 'x', 'y', 'requirement', 'serviceTime'))
        self.customerInfo: list[customer] = []  # 客户信息（依次为名称、X坐标、Y坐标、货物需求、服务时间）
        self.dis: list[list] = []  # 客户间距离
        self.carCapacity: int = 0  # 车辆最大容量
        self.minDistance: int = 0  # 最短距离
        self.population: int = 0  # 节点数量

        self.io(filePath, customer)
        self.calcDis()

    def io(self, filePath, infoType):
        """
        * 加载数据
        * 读取数据文件，再根据数据内容
        * 依次读取customerInfo, carCapacity
        """
        customerInfo = []
        with open(filePath) as f:
            # 按行读取内容
            text = f.readlines()
            for i in range(len(text)):
                # 读取结点数
                if "DIMENSION" in text[i]:
                    index = text[i].index(":") + 1
                    self.population = eval(text[i][index:])
                    customerInfo = [
                        [0 for _ in range(2)] for _ in range(self.population)]
                # 读取车辆最大容量
                if "CAPACITY" in text[i]:
                    index = text[i].index(":") + 1
                    self.carCapacity = eval(text[i][index:])
                # 读取最短距离
                if "DISTANCE" in text[i]:
                    index = text[i].index(":") + 1
                    self.minDistance = eval(text[i][index:])

                if text[i] == "NODE_COORD_SECTION\n":
                    # 读取客户位置
                    i = i + 1
                    while text[i] != "DEMAND_SECTION\n":
                        info = text[i].split()
                        info = [eval(info[x]) for x in range(len(info))]
                        customerInfo[info[0]] = info[1:]
                        i = i + 1

                    # 读取客户需求
                    i = i + 1
                    while text[i] != "SVC_TIME_SECTION\n":
                        info = text[i].split()
                        info = [eval(info[x]) for x in range(len(info))]
                        customerInfo[info[0]].append(
                            max(info[1:]) if max(info[1:]) != -1 else 0)
                        i = i + 1

                    # 读取客户服务时间
                    i = i + 1
                    while text[i] != "DEPOT_SECTION\n":
                        info = text[i].split()
                        info = [eval(info[x]) for x in range(len(info))]
                        customerInfo[info[0]].append(max(info[1:]))
                        i = i + 1

                    # 读取仓库坐标
                    i = i + 1
                    info = text[i].split()
                    info = [eval(info[x]) for x in range(len(info))]
                    customerInfo[0] = info
                    i + 1

                    # 初始化仓库需求
                    info = text[i].split()
                    info = [eval(info[x]) for x in range(len(info))]
                    customerInfo[0].append(info[0] if info[0] != -1 else 0)
                    # 初始化仓库服务时间
                    if len(customerInfo[0]) == 3:
                        customerInfo[0].append(0)

                    # 结束初始化参数
                    break

        for i, customer in enumerate(customerInfo):
            x, y, requirement, serviceTime = customer
            newCustomer = infoType(i, x, y, requirement, serviceTime)
            self.customerInfo.append(newCustomer)

    def calcDis(self):
        self.dis = list([[0 for _ in range(len(self.customerInfo))]
                         for _ in range(len(self.customerInfo))])
        for i in range(len(self.customerInfo)):
            for j in range(len(self.customerInfo)):
                distance = sqrt((self.customerInfo[i].x - self.customerInfo[j].x) ** 2 +
                                (self.customerInfo[i].y - self.customerInfo[j].y) ** 2)
                self.dis[i][j] = distance

    def getDis(self, index1, index2):
        return self.dis[index1][index2]

    def getPopulation(self):
        return self.population

    def getPosX(self, index):
        return self.customerInfo[index].x

    def getPosY(self, index):
        return self.customerInfo[index].y

    def generateRandomPaths(self, num):
        paths = []
        for _ in range(num):
            isUsed = set()
            path = list()
            while len(path) < self.population:
                customerIndex = randint(0, self.population - 1)
                if customerIndex not in isUsed:
                    isUsed.add(customerIndex)
                    path.append(customerIndex)
            paths.append(path)
        return paths


class unit(object):
    def __init__(self, path, length):
        self.solution = path
        self.length = length


class AntColonyAlgorithm(object):
    def __init__(self, filePath, population, alpha, beta, sigma, Q, inition, iteration):
        self.customerInfo = customerInfomation(filePath)
        self.population = population
        self.alpha = alpha
        self.beta = beta
        self.sigma = sigma
        self.increasement = Q
        self.iteration = iteration

        cityNum = self.customerInfo.getPopulation()
        self.cityMatrix = [
            [inition for _ in range(cityNum)] for _ in range(cityNum)]

        self.ants = []
        solutions = self.customerInfo.generateRandomPaths(self.population)
        for solution in solutions:
            self.ants.append(unit(solution, self.calcLength(solution)))

        self.globalBest = min(self.ants, key=attrgetter('length'))
        self.costRecord = []

    def run(self):
        for it in tqdm(range(self.iteration)):
            for ant in self.ants:
                self.updateMatrix(ant)
            self.ants.clear()
            for i in range(self.population):
                ant = self.generateNewAnt()
                while len(ant.solution) < self.customerInfo.getPopulation():
                    ant.solution = self.choosePath(ant.solution)
                ant.length = self.calcLength(ant.solution)
                self.ants.append(ant)

            partialBest = min(self.ants, key=attrgetter('length'))
            if partialBest.length < self.globalBest.length:
                self.globalBest = partialBest
            self.costRecord.append(self.globalBest.length)

    def calcLength(self, path):
        dis = 0
        for i in range(len(path) - 1):
            dis += self.customerInfo.getDis(path[i], path[i+1])
        dis += self.customerInfo.getDis(path[0], path[-1])
        return dis

    def generateNewAnt(self):
        newAnt = unit([randint(0, self.customerInfo.getPopulation()-1)], 0)
        return newAnt

    def choosePath(self, solution):
        tail = solution[-1]
        fitness = []
        rnd = random()
        for i in range(len(self.cityMatrix[tail])):
            if i in solution:
                fitness.append(0)
                continue
            fitness.append(self.cityMatrix[tail][i] ** self.alpha /
                           (self.customerInfo.getDis(tail, i) ** self.beta))
        rnd *= sum(fitness)
        for i in range(len(fitness)):
            if rnd <= fitness[i]:
                solution.append(i)
                break
            rnd -= fitness[i]

        return solution

    def updateMatrix(self, ant):
        solution = ant.solution
        length = ant.length
        for i in range(len(solution) - 1):
            self.cityMatrix[solution[i]][solution[i+1]] *= self.sigma
            self.cityMatrix[solution[i]][solution[i+1]
                                         ] += self.increasement / length
            self.cityMatrix[solution[i+1]][solution[i]] *= self.sigma
            self.cityMatrix[solution[i+1]][solution[i]
                                           ] += self.increasement / length
        self.cityMatrix[solution[-1]][solution[0]] *= self.sigma
        self.cityMatrix[solution[-1]][solution[0]
                                      ] += self.increasement / length
        self.cityMatrix[solution[0]][solution[-1]] *= self.sigma
        self.cityMatrix[solution[0]][solution[-1]
                                     ] += self.increasement / length

    def display(self, startTime, endTime):
        duration = endTime - startTime
        hr = duration // 3600
        minutes = (duration - hr * 3600) // 60
        seconds = duration - hr * 3600 - minutes * 60
        print(
            f'using system time: {hr}hr(s) {minutes}min(s) {seconds:.2f}s, the global best solution is following:')
        for index in self.globalBest.solution:
            print(f'{index}', end='->')
        print(f'{self.globalBest.solution[0]}')
        print(f'the cost of this solution is {self.globalBest.length:.2f}')

        plt.figure()
        plt.subplot(2, 1, 1)
        routeX, routeY = [[self.customerInfo.getPosX(index) for index in self.globalBest.solution],
                          [self.customerInfo.getPosY(index) for index in self.globalBest.solution]]
        routeX.append(routeX[0])
        routeY.append(routeY[0])
        route, = plt.plot(routeX, routeY)

        routeX, routeY = [[self.customerInfo.getPosX(index) for index in range(self.customerInfo.getPopulation())],
                          [self.customerInfo.getPosY(index) for index in range(self.customerInfo.getPopulation())]]
        customer = plt.scatter(routeX, routeY, marker='o', color='g')

        for i, _ in enumerate(routeX):
            plt.annotate(i, (routeX[i] + 0.05, routeY[i] + 0.25))

        plt.legend([customer, route], ['customers', 'route'])
        plt.xlabel('Pos X')
        plt.ylabel('Pos Y')
        plt.title('genetic algorithm for the simple TSP')

        plt.subplot(2, 1, 2)
        plt.plot([x+1 for x in range(len(self.costRecord))], self.costRecord)
        plt.xlabel('epoch')
        plt.ylabel('cost')
        plt.show()


if __name__ == '__main__':
    main()
