import numpy as np
import matplotlib.pyplot as plt

grow_results = [
                ["10",[0.36086058616638184,
                     0.35841870307922363,
                     0.34795117378234863,
                     0.3463284969329834,
                     0.3400540351867676,
                     0.3587069511413574]],
                ["20",[0.7961955070495605,
                     0.7907657623291016,
                     0.7690563201904297,
                     0.7236838340759277,
                     0.7802786827087402,
                     0.7704708576202393]],
                ["30",[1.2808208465576172,
                     1.2489426136016846,
                     1.2077925205230713,
                     1.2170779705047607,
                     1.214789628982544,
                     1.2387795448303223]],
                ["40",[2.112102746963501,
                     2.20390248298645,
                     2.1068780422210693,
                     2.2303543090820312,
                     2.168545961380005,
                     2.055896759033203]],
                ["50",[3.6414804458618164,
                     3.2569384574890137,
                     3.5307183265686035,
                     3.494738817214966,
                     3.531611919403076,
                     3.335860252380371]]
               ]

shrink_results = [
                  ["10",[0.2594926357269287,
                       0.26140642166137695,
                       0.2395944595336914,
                       0.2559638023376465,
                       0.2565181255340576,
                       0.27053165435791016]],
                  ["20",[0.517341136932373,
                       0.4950237274169922,
                       0.5217747688293457,
                       0.522381067276001,
                       0.5027737617492676,
                       0.5285279750823975]],
                  ["30",[0.7873885631561279,
                       0.7744555473327637,
                       0.775585412979126,
                       0.7676839828491211,
                       0.773125171661377,
                       0.7681219577789307]],
                  ["40",[1.0043137073516846,
                       1.0343692302703857,
                       1.0021848678588867,
                       1.0286791324615479,
                       1.0156052112579346,
                       1.0309827327728271]],
                  ["50",[1.308018445968628,
                       1.3330845832824707,
                       1.2963535785675049,
                       1.288100242614746,
                       1.3010177612304688,
                       1.2826368808746338]],
                 ]


def create_plot(labels, avgs, stds, title, ylim=4):
    """ Create and show plot """
    fig = plt.figure()
    plt.errorbar(labels,
                 avgs,
                 yerr=stds,
                 label="plot",
                 linestyle='None',
                 marker='.',
                 capsize=5)
    plt.title(title)
    plt.ylim([0, ylim])
    plt.ylabel("Time (secs)")
    plt.xlabel("Number of nodes")
    plt.show()



def main():
    grow_label = []
    grow_avgs = []
    grow_stds = []
    for set in grow_results:
        grow_label.append(set[0])
        grow_avgs.append(np.mean(set[1]))
        grow_stds.append(np.std(set[1]))
    create_plot(grow_label, grow_avgs, grow_stds, "Plot of average grow time", ylim=4)

    shrink_label = []
    shrink_avgs = []
    shrink_stds = []
    for set in shrink_results:
        shrink_label.append(set[0])
        shrink_avgs.append(np.mean(set[1]))
        shrink_stds.append(np.std(set[1]))
    create_plot(shrink_label, shrink_avgs, shrink_stds, "Plot of average shrink time to half",  ylim=1.5)


if __name__ == "__main__":
    main()
