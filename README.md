# ML-DEECo: Machine Learning-enabled Component Model for Dynamically Adapting Systems

This is an accompanying repository to the paper *ML-DEECo: Machine Learning-enabled Component Model for Dynamically Adapting Systems* by Milad Abdullah, Michal Töpfer, Tomáš Bureš, Petr Hnětynka and Martin Kruliš.

## Contents

There are several folders in this repository:

* [`ml_deeco`](ml_deeco) &ndash; implementation of the ML-DEECo framework.
* [`ml_deeco_example`](ml_deeco_example)
  * [`simple_example`](ml_deeco_example/simple_example) &ndash; a simple example showing basic usage of the ML-DEECo framework.
  * [`all_example`](ml_deeco_example/all_example) &ndash; example of all predictions defined in the taxonomy (serves mainly as a test of the implementation).
* [`drone_charging_example`](drone_charging_example) &ndash; the example showcased throughout the paper (with a replication package).

## Limitations and Threats to Validity

We list the most important ones below. We organize the threats to validity based on the schema in [RH2009], where the validity classes are defined as follows:
 * construct validity,
 * internal validity,
 * external validity, and
 * reliability.

*Construct validity:* We construct our validation on the assumption that by providing the data collection and ML, the ML-DEECo framework saves coding effort for the types of predictions identified in the paper in Section III.A. This could potentially be false, though we did our best to make the meta-model and the corresponding Python API easy to use. Also, we provide several examples that show that different predictors can indeed be easily deployed just with a couple of lines in Python.

*Internal validity:* To show that the framework has the potential to improve self-adaptive systems by introducing ML-based estimation, we made the experiment described in the paper in Section IV.C. We use two metrics as a measure of the improvement: the total amount of damaged crops and the number of drones that did not run out of battery till the end of the simulation. A potential threat here is that there is a hidden unknown factor that has a significant influence on the results. We mitigated this threat by the following: (1) We used exactly the same component and ensemble definitions for both the baseline and the ML-based architecture; the only difference was the value of the `waitingTime`, which was set to 0 in the baseline and to the value of the estimator in the ML-based solution. (2) We made several experiments in which we varied individual parameters of the simulation and observed the effect on these metrics to ensure that we did not see any unexpected or random effects. 

*External validity:* We attempted to ensure our solution is general by basing it on the taxonomy of predictions (Section III.A}), which is independent of our running example and is built as a combination of generally accepted abstractions. However, the use case we show and the simulation we did cannot by themselves guarantee generalizability. They serve rather as proof of feasibility. To show the full generalizability of our results, we would have to apply our approach on larger case studies. This is beyond the scope of this paper and constitutes future work.

*Reliability:* Though coming from an EU project with multiple partners, the implementation of the use-case we used for demonstration was created by us, including the baseline and the ML-based solution. This makes our results dependent on us. We ensured the difference between the baseline and the ML-based solution is only in the use of the estimator. However, this still makes our results only an indicator of the potential improvement and a feasibility case. They do not permit quantification of an expected improvement in other applications.


[RH2009]  P. Runeson and M. Höst, “Guidelines for conducting and reporting case study research in software engineering,” Empirical Software Engineering, vol. 14, no. 2, pp. 131–164, Apr. 2009. 
