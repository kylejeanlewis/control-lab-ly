# Parallel Spin Coater Control
This package provides the controls for the parallel spin-coaters.

# Dependencies
- pandas
- plotly
- datetime, time
- threading
- serial

# Modules
- \(main\) main
- \(helper\) gantt, routines, spinutils

## gantt
- _function_ **read_log** \(activity_log, connects\)   

    Reads the log files and separate lines by tools   
    \- activity_log: file path of log file   
    \- connects: connection information about the devices / tools

    Returns: list of lines in log file, dictionary of logs for each tool

- _function_ **gantt_plotter** \(log_output, tool_log, show_plot=False, save_plot=False\)   

    Plots the gantt chart using the log files, in relative time
    \- log_output: list of lines in log file   
    \- tool_log: dictionary of logs for each tool   
    \- show_plot: whether to show the gantt chart   
    \- save_plot: whether to save the gantt chart

    Returns: plot figure (plotly.graph_objects.figure)

## routines
- _function_ **log_now** \(string, force_print=False\)   

    Add log with timestamp
    \- string: log message   
    \- force_print: whether to force display message in console   

    Returns: log message with timestamp

- _function_ **start_log** \(p_log, log_out\)   

    Start logging the whole process   
    \- p_log: whether to print the log messages in console   
    \- log_out: list object to which log messages are stored

    Returns: None

- _function_ **write_log** \(out, connects\)   

    Write logs into txt files   
    \- out: list of log messages   
    \- connects: dataframe of connection information

    Returns: dictionary of log messages with tool names as keys

- _class_ **Spinner** \(order, position, spin\)   

    'Spinner' class contains methods to control the spin coater unit.   
    \- order: order from left to right   
    \- position: physical position \(mm\)   
    \- spin: connection to Arduino

    - _method_ **execute** \(t_soak, s_spin, t_spin\)   

        Executes the soak and spin steps   
        \- t_soak: soak time   
        \- s_spin: spin speed   
        \- t_spin: spin time

        Returns: None

    - _method_ **soak** \(seconds\)   

        Executes the soak step   
        \- seconds: soak time

        Returns: None

    - _method_ **spin_off** \(speed, seconds\)   

        Executes the spin step   
        \- speed: spin speed   
        \- seconds: spin time

        Returns: None

- _class_ **Syringe** \(order, offset, capacity, pump\)   

    'Syringe' class contain methods to control the pump and the valve unit.   
    \- order: order from left to right   
    \- offset: offset from the cnc arm \(mm\)   
    \- capacity: capacity of syringe   
    \- pump: connection to Arduino

    - _method_ **aspirate** \(vol, speed=300\)   

        Adjust the valve and aspirate reagent   
        \- vol: volume   
        \- speed: speed of pump rotation

        Returns: None
        
    - _method_ **dispense** \(vol, speed=300, force_dispense=False\)   

        Adjust the valve and dispense reagent   
        \- vol: volume   
        \- speed: speed of pump rotation   
        \- force_dispense: continue with dispense even if insufficient volume in syringe

        Returns: None

    - _method_ **empty** \(\)   

        Adjust the valve and empty syringe

        Returns: None
    
    - _method_ **fill** \(reagent, vol=None\)   

        Adjust the valve and fill syringe with reagent   
        \- reagent: reagent to be filled in syringe   
        \- vol: volume

        Returns: None

- _class_ **Setup** \(conn_df, syringe_offsets, syringe_capacities, fill_position, dump_position, spin_positions\)   

    'Setup' class contains methods to control the cnc arm, as well as coordinate the other units.   
    \- conn_df: dataframe containing details for connections to Arduinos   
    \- syringe_offsets: list of syringe offsets with respect to cnc arm   
    \- syringe_capacities: list of syringe capacities   
    \- fill_position: position of fill station   
    \- dump_position: position of dump station   
    \- spin_positions: position of spinners

    - _method_ **align** \(syringe_offset, position\)   

        Position the relevant syringe with the relevant spinner / station   
        \- syringe_offset: the offset between syringe and cnc arm   
        \- position: location of the relevant spinner / station \(< 0\)

        Returns: new x position of cnc arm
    
    - _method_ **coat** \(spinner, syringe, vol, t_soak, s_spin, t_spin, new_thread=True, rest_home=True\)   

        Aligns the syringe and perform a spincoating step   
        \- spinner: relevant spinner object   
        \- syringe: relevent syringe object   
        \- vol: volume   
        \- t_soak: soak time   
        \- s_spin: spin speed   
        \- t_spin: spin time   
        \- new_thread: whether to run the spinner in a separate work thread   
        \- rest_home: whether to send cnc arm to home during rest

        Returns: new work thread or None

    - _method_ **connect** \(df\)   

        Establish connections with the hardware   
        \- df: config dataframe

        Returns: None

    - _method_ **empty_syringes** \(syringe_nums, manual=False\)   

        Empty relevant syringes   
        \- syringe_nums: list of syringes to be emptied   
        \- manual: supervised emptying of syringes

        Returns: None

    - _method_ **fill_syringes** \(syringe_nums, reagents, vol, manual=False\)   

        Fill relevant syringes   
        \- syringe_nums: list of syringes to be filled   
        \- reagents: list of reagents to be filled   
        \- vol: list of volumes of each reagent to fill   
        \- manual: supervised filling of syringes

        Returns: None

    - _method_ **home** \(\)   

        Moves cnc arm to home position

        Returns: None

    - _method_ **run_diagnostic** \(\)   

        Perform diagnostic tests to test connections and hardware

        Returns: None


- _class_ **Controller** \(dfs\)   

    'Controller' class contains high-level methods to take in instructions and conduct the steps.   
    \- dfs: dictionary of dataframes extracted from xlsx file \(config and params\)

    - _method_ **assign_plans** \(plans\)   

        Assign the steps to the respective spinners   
        \- plans: list of plan labels for the spinners in order

        Returns: None

    - _method_ **check_overrun** \(start_time, timeout\)   

        Check whether time has been overrun   
        \- start_time: start of experiment   
        \- timeout: max time allowed

        Returns: bool

    - _method_ **check_setup** \(\)   

        Checks the setup of the variables, such as number of spin positions with spin connections, and number syringes with number of reagents

        Returns: None

    - _method_ **give_instructions** \(spinner, steps, new_thread=True, rest_home=True\)   

        Queue / send instructions to spinner   
        \- spinner: relevant Spinner object   
        \- steps: dataframe of remaining steps   
        \- new_thread: whether to start a new thread   
        \- rest_home: whether to send cnc arm to home during rest

        Returns: None

    - _method_ **prepare_setup** \(manual=False\)   
    
        Prepare the setup by filling the syringes   
        \- manual: supervised filling of syringes

        Returns: None

    - _method_ **reset_setup** \(manual=True, home_only=True\)   

        Return the setup to its initial positions and states   
        \- manual: supervised emptying of syringes   
        \- home_only: whether to only send cnc arm to home position, without emptying syringes

        Returns: None

    - _method_ **run_experiment** \(timeout=None, mode='scanning'\)   

        Run the experiment   
        \- timeout: max time before halting (in s)   
        \- mode:   
        - 'preempt': moves cnc arm to spinner with earliest estimated completion time while it is busy
        - 'scanning': continuously checks which spinner is free before moving cnc arm
        - 'sequential': non-parallel excecution

        Returns: None

    - _method_ **save_current_state** \(reset=False\)   

        Save the current state of the syringe volumes and cnc arm position   
        \- reset: whether to reset the volumes in syringes and position of cnc arm

        Returns: list of strings

    - _method_ **scheduler_preempt** \(\)   

        Scheduler that preempts the next available spinner and moves cnc arm in anticipation

        Returns: None

    - _method_ **scheduler_scanning** \(\)   

        Scheduler that scans for the next available spinner and moves cnc arm once spinner is freed up

        Returns: None

    - _method_ **scheduler_sequential** \(start_time, timeout\)   
    
        Scheduler that performs all steps sequentially (i.e. non-parallel)   
        \- start_time: start time for experiment   
        \- timeout: max time before halting (in s)

        Returns: None

## spinutils
- _class_ **macros**
    - _method_ **list_serial** \(\)
    - _method_ **open_serial** \(\)

- _class_ actuate
    - _method_ **run_speed** \(mcu, speed\)
    - _method_ **run_spin_step** \(mcu, speed, run_time\)
    - _method_ **run_pump** \(mcu, speed\)
    - _method_ **run_solenoid** \(mcu, state\)
    - _method_ **dispense** \(mcu, pump_speed, prime_time, drop_time, channel\)
    - _method_ **home_dispense** \(mcu\)
    - _method_ **move_dispense_rel** \(mcu, current_x, distance\)
    - _method_ **move_dispense_abs** \(mcu, current_x, position\)
