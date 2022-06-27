# Introducing Estimators&mdash;Abstraction for Easy ML Employment in Self-adaptive Architectures

This is an accompanying repository to the paper *Introducing Estimators&mdash;Abstraction for Easy ML Employment in Self-adaptive Architectures* by Milad Abdullah, Michal Töpfer, Tomáš Bureš, Petr Hnětynka, Martin Kruliš, and František Plášil.


## Contents

There are several folders in this repository:

* [`ml_deeco`](ml_deeco) &ndash; implementation of the ML-DEECo framework.
* [`ml_deeco/examples`](ml_deeco/examples)
  * [`simple_example`](ml_deeco/examples/simple_example) &ndash; a simple example showing basic usage of the ML-DEECo framework.
  * [`all_example`](ml_deeco/examples/all_example) &ndash; example of all predictions defined in the taxonomy (serves mainly as a test of the implementation).
* [`drone_charging_example`](drone_charging_example) &ndash; the example showcased throughout the paper (with a replication package).
* [`meta-models`](meta-models) &ndash; figures included in this readme.

Furthermore, this readme file contains supplementary content to the paper:

* [Estimators semantics and meta-models](#estimators-semantics-and-meta-models)
* [Mapping to Python](#mapping-to-python)
* [Limitations and Threats to Validity](#limitations-and-Threats-to-Validity)

## Estimators semantics and meta-models

In this section, we show how to integrate the ability to make predictions and use them in the meta-model of an ensemble-based component model.

We start with a (simplified due to the space constraints) meta-model describing core concepts of components and ensembles from the DEECo ensemble-based component model [B2013].

![Ensembles meta-model](meta-models/ensembles-meta-model.png "Ensembles meta-model")

Now we show the meta-model of the concepts discussed in Sections 3.A and 3.B of the paper and how they are incorporated to DEECo (technically, this meta-model is a package that extends the core meta-model &ndash; the gray dashed elements are defined in the core meta-model).

![Estimate meta-model](meta-models/estimate-meta-model.png "Estimate meta-model")

The core element is the `Estimate`, which represents values to be learned together with all the necessary inputs, guards, etc.
Following the "where" dimension, the `Estimate` can be attached to a component (each component can have multiple `Estimate`s &ndash; each for a different data field), an ensemble, or a pair ensemble-component.

The `Estimate` itself is parameterized by the `EstimatorModel`, which defines parameters for the underlying neural network and thus the estimate implementation and behavior.
Each `Estimate` can have multiple `Input`s (training features), i.e., fields of the component needed for training and prediction. We distinguish here between numerical and categorical features, which influences whether the value is used as-is (possibly normalized) or whether one-hot encoding (in the case of categorical features) is used.

The `Estimate` is further specialized to distinguish between the options in the "what" dimension. In the *value* case (represented by subclass `ValueEstimate`), it specifies a target, which denotes the truth values that are to be predicted by the estimator. This can be either numerical or categorical value computed based on the component fields. For numerical values, we use the `RegressionEstimate` subclass of `ValueEstimate`, and for categorical values, we use the `ClassificationEstimate`. The number of time steps we want to predict into the future is set by the `inTimeSteps` attribute of `ValueEstimate`.

For the *time-to-condition* case, there is another subclass of `Estimate` &ndash; `TimeToConditionEstimate` &ndash; which specifies a required condition.

The `Estimate` further defines a guard predicate (over component fields), which determines if inputs and outputs (i.e., the target feature or the result of the condition) are valid and thus can be used to collect data for training the estimator.

Such a description of an estimator is enough for automated data collection and training. The semantics of the modeling concepts in the data collection phase is as follows. 

In the case of the `ValueEstimate`, we perform the following actions in every time step:

* We collect the inputs and the current time provided that the guard condition on inputs is true.
* We collect the outputs (represented by class `Target`), provided that the guard condition on the output is true. We associate the output with inputs that were collected `inTimeSteps` time steps ago. If the guard condition on the output is false, we discard the inputs recorded `inTimeSteps` time steps ago.

In case of the `TimeToConditionEstimate`, we perform the following action in every time step:

* We collect the inputs and the current time to a buffer provided that the guard condition on inputs is true.
* If the condition specified by the `Condition` is true, we
associate all the inputs collected in the buffer (as per step \#1) with the difference between the current time and the time of the input in the buffer. We clear the buffer.

### Examples

#### Component

To illustrate the concepts, we show an instance of the meta-model for the drone component of the running example.

![Example of drone component](meta-models/drone-example.png "Example of drone component")

The drone has two fields &ndash; `Battery` containing the current state of battery energy and `State` expressing the current operational state of the drone.
The drone has attached a single `TimeToConditionEstimate` predicting how long it will take for the drone to get into the `CHARGING` state (thus the `Condition` is a simple predicate checking equality of the `State` to the `CHARGING` value).
The estimate has two inputs &ndash; `BatteryEnergyInput` and `DroneStateInput` (the former of the numeric kind while the latter of the categorical kind).

Similarly, in the running example, the drone has the `RegressionEstimate` for predicting battery energy.

#### Ensemble

We also show an instance of the `EnsembleType` &ndash; particularly the `DroneChargingAssignment`, which groups and coordinates drones waiting for a given charger.

![Example of drone charging ensemble](meta-models/ensemble-example.png "Example of drone charging ensemble")

It has a single static role for an associated `Charger` (with cardinality $1$) and a single dynamic role `Drones` (for the grouped drones) with the multiple cardinality without any upper limit (i.e., it can possibly group all the available drones). 
The selector of the role selects drones that are in need of charging.
As the cardinality is unlimited, there is no utility function defined (as all the drones can be assigned to the role).

## Mapping to Python

As a proof of concept, we developed an open-source Python-based framework (available in the [`ml_deeco`](ml_deeco) folder) that realizes the approach described in the paper. 
The framework features API for defining components, ensembles, and the estimators&mdash;thus providing an internal domain-specific language for the design of ensemble-based component systems that employ ML[^1].

The framework uses decorators[^2] to define inputs, expected outputs (value and condition), and guards for the estimators.

Both the component and ensemble types are defined as classes. For illustration, consider the fragment of the `Drone` component type shown in Listing below.
The class extends the predefined `Component` class. 
The fields of the component are defined in the constructor (the `__init__` method). 

The `Drone` class showcases two estimators&mdash;one for battery level estimation and another for estimating the time till the drone starts charging.

The battery level estimator uses the current battery level `battery` and the operational mode of the drone `mode` as inputs and predicts `battery` in the future. The definition of the estimator is split into three parts: (a) The basic structure of the neural network and storage for the collected data (lines 1&ndash;5).  
(b) The declaration of the estimate fields in the component 
(lines 9&ndash;10). (c) The definition of inputs, output, and guards. These are realized as decorators on component fields and getter functions of `Drone`.

Namely, the decorators are as follows.
The `@futureBatteryEstimate.input()` decorates methods returning input values. The inputs indicate whether they are numeric values or categorical ones.
The output is similarly decorated with the `@futureBatteryEstimate.output()` (line 27).
The `@futureBatteryEstimate.inputsValid()` and `@futureBatteryEstimate.outputsValid()` denote guards, i.e., conditions under which the inputs and outputs can be used for training the estimators (in this particular case, the drone must not be in the TERMINATED mode&mdash;line 31).

The definition of the `timeToChargingModeEstimate` estimator is very similar. The only difference is that instead of defining the output, a condition is provided (line 38).


<pre class="python" style="font-family:monospace;"><ol><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">droneBatteryEstimator <span style="color: #66cc66;">=</span> NeuralNetworkEstimator<span style="color: black;">&#40;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    hidden_layers<span style="color: #66cc66;">=</span><span style="color: black;">&#91;</span><span style="color: #ff4500;">32</span><span style="color: #66cc66;">,</span> <span style="color: #ff4500;">32</span><span style="color: black;">&#93;</span><span style="color: #66cc66;">,</span>  </div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">      <span style="color: #808080; font-style: italic;"># two hidden layers with 32 neurons</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    name<span style="color: #66cc66;">=</span><span style="color: #483d8b;">&quot;Drone battery&quot;</span></div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;"><span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">timeToChargingEstimator <span style="color: #66cc66;">=</span> ...</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;"><span style="color: #ff7700;font-weight:bold;">class</span> Drone<span style="color: black;">&#40;</span>Component<span style="color: black;">&#41;</span>:</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    futureBatteryEstimate <span style="color: #66cc66;">=</span> ValueEstimate<span style="color: black;">&#40;</span><span style="color: black;">&#41;</span>.<span style="color: black;">inTimeStepsRange</span><span style="color: black;">&#40;</span><span style="color: #ff4500;">1</span><span style="color: #66cc66;">,</span> <span style="color: #ff4500;">200</span><span style="color: black;">&#41;</span>.<span style="color: black;">using</span><span style="color: black;">&#40;</span>droneBatteryEstimator<span style="color: black;">&#41;</span></div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    timeToChargingModeEstimate <span style="color: #66cc66;">=</span> TimeEstimate<span style="color: black;">&#40;</span><span style="color: black;">&#41;</span>.<span style="color: black;">using</span><span style="color: black;">&#40;</span>timeToChargingEstimator<span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> <span style="color: #0000cd;">__init__</span><span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: #66cc66;">,</span> location<span style="color: black;">&#41;</span>:</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #008000;">self</span>.<span style="color: black;">battery</span> <span style="color: #66cc66;">=</span> <span style="color: #ff4500;">1</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #008000;">self</span>.<span style="color: black;">mode</span> <span style="color: #66cc66;">=</span> DroneMode.<span style="color: black;">IDLE</span></div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #808080; font-style: italic;"># more code</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>futureBatteryEstimate.<span style="color: #008000;">input</span><span style="color: black;">&#40;</span>NumericFeature<span style="color: black;">&#40;</span><span style="color: #ff4500;">0</span><span style="color: #66cc66;">,</span> <span style="color: #ff4500;">1</span><span style="color: black;">&#41;</span><span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>timeToChargingModeEstimate.<span style="color: #008000;">input</span><span style="color: black;">&#40;</span>NumericFeature<span style="color: black;">&#40;</span><span style="color: #ff4500;">0</span><span style="color: #66cc66;">,</span> <span style="color: #ff4500;">1</span><span style="color: black;">&#41;</span><span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> battery<span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: black;">&#41;</span>:</div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #ff7700;font-weight:bold;">return</span> <span style="color: #008000;">self</span>.<span style="color: black;">battery</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>futureBatteryEstimate.<span style="color: #008000;">input</span><span style="color: black;">&#40;</span>CategoricalFeature<span style="color: black;">&#40;</span>DroneMode<span style="color: black;">&#41;</span><span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>timeToChargingModeEstimate.<span style="color: #008000;">input</span><span style="color: black;">&#40;</span>CategoricalFeature<span style="color: black;">&#40;</span>DroneMode<span style="color: black;">&#41;</span><span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> drone_mode<span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: black;">&#41;</span>:</div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #ff7700;font-weight:bold;">return</span> <span style="color: #008000;">self</span>.<span style="color: black;">mode</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>futureBatteryEstimate.<span style="color: black;">output</span><span style="color: black;">&#40;</span>NumericFeature<span style="color: black;">&#40;</span><span style="color: #ff4500;">0</span><span style="color: #66cc66;">,</span> <span style="color: #ff4500;">1</span><span style="color: black;">&#41;</span><span style="color: black;">&#41;</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> battery<span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: black;">&#41;</span>:</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #ff7700;font-weight:bold;">return</span> <span style="color: #008000;">self</span>.<span style="color: black;">battery</span></div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>futureBatteryEstimate.<span style="color: black;">inputsValid</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>futureBatteryEstimate.<span style="color: black;">outputsValid</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>timeToChargingModeEstimate.<span style="color: black;">inputsValid</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>timeToChargingModeEstimate.<span style="color: black;">outputsValid</span></div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> not_terminated<span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: black;">&#41;</span>:</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #ff7700;font-weight:bold;">return</span> <span style="color: #008000;">self</span>.<span style="color: black;">mode</span> <span style="color: #66cc66;">!=</span> DroneMode.<span style="color: black;">TERMINATED</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #66cc66;">@</span>timeToChargingStateEstimate.<span style="color: black;">condition</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> is_charging_state<span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: black;">&#41;</span>:</div></li><li style="font-weight: bold; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #ff7700;font-weight:bold;">return</span> <span style="color: #008000;">self</span>.<span style="color: black;">mode</span> <span style="color: #66cc66;">==</span> DroneMode.<span style="color: black;">CHARGING</span></div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">&nbsp;</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">    <span style="color: #ff7700;font-weight:bold;">def</span> actuate<span style="color: black;">&#40;</span><span style="color: #008000;">self</span><span style="color: black;">&#41;</span>:</div></li><li style="font-weight: normal; vertical-align:top;"><div style="font: normal normal 1em/1.2em monospace; margin:0; padding:0; background:none; vertical-align:top;">        <span style="color: #808080; font-style: italic;"># more code</span></div></li></ol></pre>


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

[B2013] Tomas Bures, Ilias Gerostathopoulos, Petr Hnetynka, Jaroslav Keznikl, Michal Kit, and Frantisek Plasil. 2013. DEECO: an ensemble-based component system. In Proceedings of the 16th International ACM Sigsoft symposium on Component-based software engineering (CBSE '13). Association for Computing Machinery, New York, NY, USA, 81–90. DOI:https://doi.org/10.1145/2465449.2465462

[^1]: In our previous works, we were using the Scala-based DSL for ensembles specification. While the Scala language allows for much higher flexibility in designing DSLs, Python has better support in the area of ML, and, importantly, as it is currently one of the most popular programming languages, a Python-based DSL has much higher chances for further usage and adoption.

[^2]: A decorator in Python is a function/method that enhances the functionality  of the function/method over which is applied (without modifying it) and assigns the result to the identifier of the original function/method&mdash;see https://www.python.org/dev/peps/pep-0318/