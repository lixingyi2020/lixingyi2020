# -*- coding: utf-8 -*-
"""
Created on Wed Jun  7 10:57:03 2023

@author: Xingyi Li
"""

from datetime import datetime, timedelta, date
import json
import pandas

ONE_DAY_IN_SEC = 86400
YYYYMMDD = '%Y%m%d'
YMDHMS = '%Y%m%d %H:%M:%S'

# Scheduling Indicator
SI_TIME = 0
SI_KEY_DATE = 1
SI_FACTORY_CALENDAR = 2
SI_COUNTER_BASED = 3
SI_MULTI_COUNTER = 4

# SCHEDULE_STATUS
SS_HOLD = 'Hold'
SS_FIXED = 'Fixed'
SS_SKIPPED = 'Skipped'
SS_CALLED = 'Called'
SS_COMPLETED = 'Completed'
SS_LOCKED = 'Locked'
SS_SAVE_TO_CALL = 'Save to call'

# SCHEDULE_TYPES
ST_NEW_START = 'N'
ST_SCHEDULED = 'T'
ST_MANUAL = 'M'
ST_CYCLE_START = 'Z'

NULL_DATE = datetime.strptime('19000101', YYYYMMDD).date()
TABLE_SCHEDULE = 'MHIS.json'
TABLE_MEASURING_DOC = 'IMRG.json'

SYSTEM = None

HOLIDAYS = ['20230501', '20230502', '20230503', '20230507',
            '20230513', '20230513', '20230520', '20230521',
            '20230527', '20230528', '20230603', '20230604',
            '20230610', '20230611', '20230617', '20230618',
            '20230622', '20230623', '20230624', '20230701',
            '20230702', '20230708', '20230709', '20230715',
            '20230716', '20230722', '20230723', '20230729',
            '20230730', '20230805', '20230806', '20230812',
            '20230813', '20230819', '20230820', '20230826',
            '20230902', '20230903', '20230909', '20230910',
            '20230916', '20230917', '20230923', '20230924',
            '20230929', '20230930', '20231001', '20231002',
            '20231003', '20231004', '20231005', '20231006']


class MonthDelta:
    """Number of months offset from a date or datetime.

    MonthDeltas allow date calculation without regard to the different lengths
    of different months. A MonthDelta value added to a date produces another
    date that has the same day-of-the-month, regardless of the lengths of the
    intervening months. If the resulting date is in too short a month, the
    last day in that month will result:

        date(2008,1,30) + MonthDelta(1) -> date(2008,2,29)

    MonthDeltas may be added, subtracted, multiplied, and floor-divided
    similarly to timedeltas. They may not be added to timedeltas directly, as
    both classes are intended to be used directly with dates and datetimes.
    Only ints may be passed to the constructor. MonthDeltas are immutable.

    NOTE: in calculations involving the 29th, 30th, and 31st days of the
    month, MonthDeltas are not necessarily invertible [i.e., the result above
    would not imply that date(2008,2,29) - MonthDelta(1) -> date(2008,1,30)].
    """
    __slots__ = ('__months',)

    def __init__(self, months=1):
        if not isinstance(months, int):
            raise TypeError('months must be an integer')
        self.__months = months
    def months(self):
        return self.__months
    months = property(months)
    def __repr__(self):
        try:
            return 'MonthDelta({0})'.format(self.__months)
        except AttributeError:
            return 'MonthDelta(' + str(self.__months) + ')'
    def __str__(self):
        return str(self.__months) + ' month' + ((abs(self.__months) != 1
                                                 and 's') or '')
    def __hash__(self):
        return hash(self.__months)
    def __eq__(self, other):
        if isinstance(other, MonthDelta):
            return (self.__months == other.months)
        return False
    def __ne__(self, other):
        if isinstance(other, MonthDelta):
            return (self.__months != other.months)
        return True
    def __lt__(self, other):
        if isinstance(other, MonthDelta):
            return (self.__months < other.months)
        return NotImplemented
    def __le__(self, other):
        if isinstance(other, MonthDelta):
            return (self.__months <= other.months)
        return NotImplemented
    def __gt__(self, other):
        if isinstance(other, MonthDelta):
            return (self.__months > other.months)
        return NotImplemented
    def __ge__(self, other):
        if isinstance(other, MonthDelta):
            return (self.__months >= other.months)
        return NotImplemented
    def __add__(self, other):
        if isinstance(other, MonthDelta):
            return MonthDelta(self.__months + other.months)
        if isinstance(other, date):
            day = other.day
            # subract one because months are not zero-based
            month = other.month + self.__months - 1
            year = other.year + month // 12
            # now add it back
            month = month % 12 + 1
            if month == 2:
                if day >= 29 and not year%4 and (year%100 or not year%400):
                    day = 29
                elif day > 28:
                    day = 28
            elif month in (4,6,9,11) and day > 30:
                day = 30
            try:
                return other.replace(year, month, day)
            except ValueError:
                raise OverflowError('date value out of range')
        return NotImplemented
    def __sub__(self, other):
        if isinstance(other, MonthDelta):
            return MonthDelta(self.__months - other.months)
        return NotImplemented
    def __mul__(self, other):
        if isinstance(other, int):
            return MonthDelta(self.__months * other)
        return NotImplemented
    def __floordiv__(self, other):
        # MonthDelta // MonthDelta -> int
        if isinstance(other, MonthDelta):
            return self.__months // other.months
        if isinstance(other, int):
            return MonthDelta(self.__months // other)
        return NotImplemented
    def __radd__(self, other):
        return self + other
    def __rsub__(self, other):
        return -self + other
    def __rmul__(self, other):
        return self * other
    def __ifloordiv__(self, other):
        # in-place division by a MonthDelta (which will change the variable's
        # type) is almost certainly a bug -- raising this error is the reason
        # we don't just fall back on __floordiv__
        if isinstance(other, MonthDelta):
            raise TypeError('in-place division of a MonthDelta requires an '
                            'integer divisor')
        if isinstance(other, int):
            return MonthDelta(self.__months // other)
        return NotImplemented
    def __neg__(self):
        return MonthDelta(-self.__months)
    def __pos__(self):
        return MonthDelta(+self.__months)
    def __abs__(self):
        return MonthDelta(abs(self.__months))
    def __bool__(self):
        return bool(self.__months)
    __nonzero__ = __bool__
    

# Singleton used as deadline time reference considering call object interval involved.
class System:
    _instance = None
    _interval = 0      # call object interval

    @staticmethod
    def get_instance(interval=0):
        if System._instance is None:
            System(interval)

        return System._instance

    def __init__(self, interval=0):
        if System._instance is not None:
            raise Exception("Error: singleton exception")
        else:
            System._instance = self
            self._interval = interval

    # used as reference for deadline monitoring considering call object interval involved
    def reference_date(self) -> date:
        return datetime.today().date() + timedelta(days=self._interval)

    def set_reference_date(self, d: date):
        self._interval = timedelta_in_days(d, datetime.today().date())


def save_data_in_json(data, filename):
    file = open(filename, 'w')
    json.dump(data, file)
    file.close()


def read_data_in_json(filename):
    file = open(filename)
    try:
        data = json.load(file)
    except Exception:
        data = {}
    finally:
        file.close()

    return data


def date2Str(d: date) -> str:
    s = d.strftime(YYYYMMDD)
    return s


def str2Date(s: str) -> date:
    if s is None or len(s) == 0:
        return datetime.strptime('19000101', YYYYMMDD).date()
    else:
        return datetime.strptime(s, YYYYMMDD).date()


def str2DateTime(s: str) -> datetime:
    if s is None or len(s) == 0:
        return datetime.strptime('19000101 00:00:00', YMDHMS)
    else:
        return datetime.strptime(s, YMDHMS)


def period2seconds(period: float, unit: str) -> int:
    if unit == "MON":
        return period * 30 * ONE_DAY_IN_SEC
    elif unit == "D":
        return period * ONE_DAY_IN_SEC
    elif unit == "H":
        return period * 60 * 60


def seconds2days(sec: int) -> float:
    return sec / ONE_DAY_IN_SEC


def period2days(period: float, unit: str) -> float:
    if unit == "MON":
        return period * 30
    elif unit == "D":
        return period
    elif unit == "H":
        return period / 24


def timedelta_in_days(d1: date, d2: date) -> int:
    d = d1 - d2
    return int(d.total_seconds()/ONE_DAY_IN_SEC)

class FactoryCalendar:
    _holidays = []

    def __init__(self, holidays: []):
        for s in holidays:
            self._holidays.append(str2Date(s))

    def holiday_count(self, start, end):
        cnt = 0
        for h in self._holidays:
            if h >= start and h <= end:
                cnt += 1
        return cnt

    def is_workday(self, d: datetime.date):
        return d not in self._holidays

    def add_workdays(self, d: datetime.date, workdays: int):
        cnt = 0
        wdc = 0
        while wdc <= workdays:
            cnt += 1
            rd = d + timedelta(days=cnt)
            if self.is_workday(rd):
                wdc += 1

        return rd
    

class MaintenancePackage:
    def __init__(self, data=[]):
        self.number = data[0]
        self.cycle = data[1]
        self.unit = data[2]
        self.cycle_text = data[3]
        self.cycle_short_text = data[4]
        self.hierachy = data[5]
        self.hierachy_text = data[6]
        self.offset = data[7]
        self.offset_text = data[8]
        self.lead_float_in_days = data[9]
        self.followup_float_in_days = data[10]
        self.operation_binded = data[11]

    def __str__(self):
        return f"{self.number}: {self.cycle}  {self.unit}, {self.hierachy_text}"

    def cycle_in_days(self):
        return period2days(self.cycle, self.unit)


class MaintenanceStrategy:
    factory_calendar = None
    packages = {}

    def __init__(self, head_data=[], pckg_data=[]):
        self.name = head_data[0]
        self.description = head_data[1]
        self.scheduling_indicator = head_data[2]
        self.unit = head_data[3]
        self.call_horizon = head_data[4]
        self.SF_late_comp = head_data[5]
        self.tolerance_late_comp = head_data[6]
        self.SF_early_comp = head_data[7]
        self.tolerance_early_comp = head_data[8]
        if head_data[9] == "":
            self.factory_calendar = None
        else:
            self.factory_calendar = FactoryCalendar(HOLIDAYS)

        for row in pckg_data:
            p = MaintenancePackage(row)
            self.packages[row[0]] = p

    def __str__(self):
        return f"{self.name}: {self.description} unit: {self.unit}"

    def min_cycle_in_days(self) -> int:
        t = []
        for p in self.packages.values():
            t.append(p.cycle_in_days())

        return min(t)

    def max_cycle_in_days(self) -> int:
        t = []
        for p in self.packages.values():
            t.append(p.cycle_in_days())

        return max(t)

    def package_sequence(self, start_offset=0, period=360) -> list:
        ps = []
        for i in range(start_offset + 1, int(start_offset + period + 1)):
            due_package = []
            for p in self.packages.values():
                if i % p.cycle_in_days() == 0:
                    due_package.append(p.number)

            if len(due_package) > 0:
                ps.append((i, due_package))
        return ps

    def due_packages(self, d: date, start_date: date, previous_offset=0) -> list:
        ps = self.package_sequence(previous_offset)
        delta = timedelta_in_days(d, start_date)
        pkg_list = []
        for t in ps:
            if previous_offset + delta >= t[0]:
                for i in t[1]:
                    pkg_list.append(self.packages[i])
                break

        return pkg_list

    def due_packages_text(self, d: date, start_date: date, previous_offset=0) -> str:
        dp = self.due_packages(d, start_date, previous_offset)
        txt = ""
        for p in dp:
            txt += p.cycle_short_text

        return txt

    # CCF doesn't play any role with offset in strategy
    def next_offset(self, start_offset=0, previous_offset=0) -> int:
        ps = self.package_sequence(start_offset, previous_offset + self.max_cycle_in_days())
        result = ps[0][0]
        for i in range(len(ps)):
            if ps[i][0] == previous_offset:
                result = ps[i + 1][0]
                break
        return result

    def get_package(self, index=1) -> MaintenancePackage:
        if type(index) == int:
            for p in self.packages.values():
                if p.number == index:
                    return p
        elif type(index) == str:
            for p in self.packages.values():
                if p.cycle_short_text == index:
                    return p
        else:
            return None
    
class MaintenancePlan:
    strategy = None

    def __init__(self, plan_params: list):
        self.SYSTEM = System.get_instance()  # init deadline reference date######

        self.plan_num = plan_params['plan_num']
        self.cycle = plan_params['cycle']
        self.cycle_unit = plan_params['cycle_unit']
        self.offset = plan_params['offset']

        self.SF_late = plan_params['SF_late']
        self.SF_late_tolerance = plan_params['SF_late_tolerance']
        self.SF_early = plan_params['SF_early']
        self.SF_early_tolerance = plan_params['SF_early_tolerance']
        self.cycle_change_factor = plan_params['cycle_change_factor']

        self.call_horizon = plan_params['call_horizon']
        self.schedule_period = plan_params['schedule_period']
        self.sp_unit = plan_params['sp_unit']
        self.completion_requirement = plan_params['completion_requirement']
        self.start_date = str2Date(plan_params['start_date'])

        self.scheduling_indicator = plan_params['scheduling_indicator']
        self.factory_calendar = plan_params['factory_calendar']
        if self.factory_calendar == '00':
            self.calendar = FactoryCalendar(HOLIDAYS)

    def __str__(self):
        return 'Plan: ' + self.plan_num + ' Cycle:' + str(self.cycle) + ' ' \
                + self.cycle_unit + ' Offset: ' + str(self.offset)

    def cycle_in_days(self) -> int:
        return self.cycle_change_factor * period2days(self.cycle, self.cycle_unit)

    def offset_in_days(self) -> int:
        return self.cycle_change_factor * period2days(self.offset, self.cycle_unit)

    def date_add_by_scheduling_indicator(self, base_date: date, delta_in_days: int) -> date:
        if self.scheduling_indicator == SI_TIME:
            return base_date + timedelta(days=delta_in_days)
        elif self.scheduling_indicator == SI_KEY_DATE:
            return base_date + MonthDelta(delta_in_days//30)
        elif self.scheduling_indicator == SI_FACTORY_CALENDAR:
            return self.calendar.add_workdays(base_date, delta_in_days)
        else:
            raise Exception(f"Error: scheduling indicator {self.scheduling_indicator} \
                            is not allowed")

    def next_plan_date(self, base_date: date, start_offset=0, previous_offset=0) -> date:
        return self.date_add_by_scheduling_indicator(base_date, self.cycle_in_days())

    def late_completion_tolerance_in_days(self) -> int:
        return self.cycle_in_days() * self.SF_late_tolerance // 100

    def early_completion_tolerance_in_days(self) -> int:
        return self.cycle_in_days() * self.SF_early_tolerance // 100

    def scheduling_end_date(self) -> date:
        return datetime.today().date() + timedelta(days=period2days(self.schedule_period,
                                                                    self.sp_unit))

    def call_horizon_expired(self, planned_date: date) -> bool:
        deadline = self.SYSTEM.reference_date()
        return (timedelta_in_days(planned_date, deadline) / self.cycle_in_days()) \
            <= ((100 - self.call_horizon) / 100)

    def call_date_by_horizon(self, plan_date: date) -> date:
        return plan_date - timedelta(days=self.cycle_in_days()) + \
               timedelta(days=self.cycle_in_days() * self.call_horizon / 100)


class StrategyPlan(MaintenancePlan):
    def __init__(self, plan_params: list, strategy: MaintenanceStrategy = None):
        super().__init__(plan_params)

        self.start_offset = 0
        if strategy is None:
            self.strategy = MaintenanceStrategy(CCF=self.cycle_change_factor)
        else:
            self.strategy = strategy
            self.strategy.CCF = self.cycle_change_factor

    def __str__(self):
        return f'Plan: {self.plan_num} Cycle:{str(self.cycle)} {self.cycle_unit} \
            Offset: {str(self.offset)} |{str(self.strategy)}'

    def next_plan_date(self, base_date: date, start_offset=0, previous_offset=0) -> date:
        next_offset = self.strategy.next_offset(start_offset, previous_offset)
        delta = (next_offset - previous_offset) * self.cycle_change_factor
        return self.date_add_by_scheduling_indicator(base_date, delta)
 
    
class CallFactory:
    def get_call(self, mplan: MaintenancePlan, data=None):
        pass


class SingleCycleCallFactory(CallFactory):
    def get_call(self, mplan: MaintenancePlan, data=None):
        return SingleCycleCall(mplan, data)


class StrategyCallFactory(CallFactory):
    def get_call(self, mplan: MaintenancePlan, data=None):
        return StrategyCall(mplan, data)


class Call:
    _plan = None
    call_num = 0
    planned_date = NULL_DATE
    call_date = NULL_DATE
    completion_date = NULL_DATE
    start_date = NULL_DATE
    last_planned_date = NULL_DATE
    prev_call_num = 0
    scheduling_type = ''
    status = ''
    previous_offset = 0
    package_num = 1
    due_package = ''

    def __init__(self, mplan: MaintenancePlan, data=None):  # data can be a list or Call object
        self._plan = mplan
        if type(data) is list:
            self.init_by_list(data)
        else:
            self.init_by_prev_call(data)

    def init_by_prev_call(self, prev_call): pass  # implemented by child classes
    def create_call_object(self): pass  # create WO, NO according to plan category

    def init_by_list(self, alist: list):
        if alist is not None:  # and len(alist) == 9:
            self.call_num = alist[0]
            self.planned_date = str2Date(alist[1])
            self.call_date = str2Date(alist[2])
            if len(alist[3]) == 0:
                self.completion_date = NULL_DATE
            else:
                self.completion_date = str2Date(alist[3])

            self.start_date = str2Date(alist[4])
            self.last_planned_date = str2Date(alist[5])
            self.prev_call_num = alist[6]
            self.scheduling_type = alist[7]
            self.status = alist[8]
            self.due_package = alist[9]
            self.prev_call = None

    def release(self):
        self.call_date = datetime.today().date()
        self.status = SS_SAVE_TO_CALL

    def complete(self, comp_date: datetime.date):
        self.completion_date = comp_date
        self.status = SS_COMPLETED

    def skip(self):
        self.status = SS_SKIPPED

    def fix(self, fix_date: date):
        self.planned_date = fix_date
        self.status = SS_FIXED

    def update(self):
        if self.scheduling_type != ST_MANUAL and \
           self.status in [SS_HOLD, SS_SAVE_TO_CALL]:
            if self.prev_call is None:
                if self._plan.offset != 0:
                    self.planned_date = self.start_date + \
                                        timedelta(days=self._plan.offset_in_days())
                else:
                    self.planned_date = self._plan.next_plan_date(self._plan.start_date)

                self.last_planned_date = NULL_DATE
            else:
                self.last_planned_date = self.prev_call.planned_date

                if self._plan.completion_requirement and self.tolerance_exceeded():
                    base_date = self.prev_call.completion_date
                else:
                    base_date = self.prev_call.planned_date

                self.planned_date = self._plan.next_plan_date(base_date) + \
                    timedelta(days=self.shifting_days())
                self.last_planned_date = self.prev_call.planned_date

            self.call_date = self.get_call_date(self.planned_date)
            self.status = self.get_status(self.planned_date)

    def tolerance_exceeded(self) -> bool:
        if self.prev_call.completion_date is NULL_DATE:
            return False
        else:
            delta = timedelta_in_days(self.prev_call.completion_date,
                                            self.prev_call.planned_date)
            if delta > 0:  # check late completion tolerance
                return self._plan.late_completion_tolerance_in_days() < delta
                pass
            else:
                return self._plan.early_completion_tolerance_in_days() < (0-delta)

    def shifting_days(self) -> int:
        if self.tolerance_exceeded():
            delta = timedelta_in_days(self.prev_call.completion_date,
                                            self.prev_call.planned_date)
            if delta > 0:
                return delta * self._plan.SF_late // 100
            else:
                return delta * self._plan.SF_early // 100
        else:
            return 0

    def prev_call_completed(self) -> bool:
        if self.prev_call is None:
            return True
        else:
            self.prev_call.completion_date != NULL_DATE

    def get_call_date(self, plan_date) -> date:
        result = self._plan.call_date_by_horizon(plan_date)
        if self._plan.call_horizon_expired(plan_date):
            if (not self._plan.completion_requirement) or \
                (self._plan.completion_requirement and
                 self.prev_call.completion_date is not NULL_DATE):
                result = datetime.today().date()

        return result

    def get_status(self, plan_date) -> str:
        result = SS_HOLD
        if self._plan.call_horizon_expired(plan_date):
            if (not self._plan.completion_requirement) or \
                (self._plan.completion_requirement and
                 self.prev_call.completion_date is not NULL_DATE):
                result = SS_SAVE_TO_CALL

        return result

    def __str__(self):
        return f'{self.call_num}, {self.planned_date}, {self.call_date}, \
            {self.completion_date}, {self.start_date},{self.last_planned_date}, \
            {self.prev_call_num}, {self.status}, {self.due_package}'

    def get_call_in_list(self) -> list:
        if self.completion_date == NULL_DATE or self.completion_date is None:
            lcd_str = ''
        else:
            lcd_str = self.completion_date.strftime(YYYYMMDD)

        if self.last_planned_date == NULL_DATE or self.last_planned_date is None:
            lpd_str = ''
        else:
            lpd_str = self.last_planned_date.strftime(YYYYMMDD)

        datarow = [self.call_num, self.planned_date.strftime(YYYYMMDD),
                   self.call_date.strftime(YYYYMMDD), lcd_str,
                   self.start_date.strftime(YYYYMMDD), lpd_str,
                   self.prev_call_num, self.scheduling_type, self.status,
                   self.due_package]
        return datarow

    def on_hold_or_fixed(self) -> bool:
        return (self.status in [SS_HOLD, SS_FIXED])


class SingleCycleCall(Call):
    def init_by_prev_call(self, prev_call: Call):
        self.prev_call = prev_call
        if prev_call is None:
            if self._plan.offset != 0:
                self.planned_date = self.start_date + timedelta(days=self._plan.offset_in_days())
            else:
                self.planned_date = self._plan.next_plan_date(self._plan.start_date)
                self.last_planned_date = NULL_DATE

            self.call_num = 1
            self.prev_call_num = 0
            self.last_planned_date = NULL_DATE
            self.scheduling_type = ST_NEW_START
        else:
            self.planned_date = self._plan.next_plan_date(prev_call.planned_date) + \
                                timedelta(days=self.shifting_days())
            self.last_planned_date = prev_call.planned_date
            self.call_num = prev_call.call_num + 1
            self.prev_call_num = prev_call.call_num
            self.scheduling_type = ST_SCHEDULED

        self.call_date = self.get_call_date(self.planned_date)
        self.status = self.get_status(self.planned_date)
        self.completion_date = NULL_DATE
        self.start_date = self._plan.start_date


# =============================================================================
# To do: include basic offset
# =============================================================================
class StrategyCall(Call):
    current_cycle_offset = 0
    previous_cycle_offset = 0

    def init_by_prev_call(self, prev_call: Call = None):
        self.prev_call = prev_call
        self.completion_date = NULL_DATE
        self.start_date = self._plan.start_date

        if self.prev_call is None:
            self.previous_cycle_offset = self._plan.start_offset
            self.current_cycle_offset = self._plan.strategy.next_offset(self._plan.start_offset,
                                                                        self.previous_cycle_offset)
            self.planned_date = self._plan.next_plan_date(self.start_date,
                                                          self._plan.start_offset,
                                                          self.previous_cycle_offset)

            if self._plan.start_offset == 0:
                self.scheduling_type = ST_NEW_START
            else:
                self.scheduling_type = ST_CYCLE_START

            self.call_num = 1
            self.prev_call_num = 0
            self.last_planned_date = NULL_DATE
        else:
            self.previous_cycle_offset = prev_call.current_cycle_offset
            self.current_cycle_offset = self._plan.strategy.next_offset(self._plan.start_offset,
                                                                        self.previous_cycle_offset)

            self.planned_date = (self._plan.next_plan_date(prev_call.planned_date,
                                                           self._plan.start_offset,
                                                           self.previous_cycle_offset)
                                 + timedelta(days=self.shifting_days()))
            self.scheduling_type = ST_SCHEDULED
            self.call_num = prev_call.call_num + 1
            self.prev_call_num = self.prev_call.call_num
            self.last_planned_date = self.prev_call.last_planned_date

        self.due_package = self._plan.strategy.due_packages_text(self.planned_date,
                                                                 self.start_date,
                                                                 self.previous_cycle_offset)
        self.call_date = self.get_call_date(self.planned_date)
        self.status = self.get_status(self.planned_date)

    def update(self):  # tbc
        super().update()
    
class Scheduler:
    call_factory: CallFactory = None

    def __init__(self, p: MaintenancePlan, call_obj_interval=0):
        SYSTEM = System.get_instance(call_obj_interval)  # init deadline reference date
        self._plan = p
        self.calls = []
        self.load_from_DB()

    def load_from_DB(self, db=TABLE_SCHEDULE):
        self.DB = read_data_in_json(db)
        try:
            call_list = self.DB[self._plan.plan_num]
        except Exception:
            call_list = []
        for row in call_list:
            _call = self.call_factory.get_call(self._plan, row)
            self.calls.append(_call)
            # set prev call
            for c in self.calls:
                if c.call_num == _call.prev_call_num:
                    _call.prev_call = c
                    break

    def save_to_DB(self, db=TABLE_SCHEDULE):
        for c in self.calls:
            if c.status == SS_SAVE_TO_CALL:
                c.create_call_object()  # create WO/NO here
                c.status = SS_CALLED

        self.DB[self._plan.plan_num] = self.get_call_list()
        save_data_in_json(self.DB, db)

    def start_scheduling(self, start_date: date):
        self._plan.start_date = start_date
        self.calls = []

        first_call = self.call_factory.get_call(self._plan, data=None)
        self.calls.append(first_call)
        self.create_following_calls(first_call, self._plan.scheduling_end_date())

    def create_following_calls(self, last_call: Call, end_date: date):
        if last_call.planned_date < end_date:
            prev_call = last_call
            while prev_call.planned_date <= end_date:
                # if last_call.scheduling_type == ST_MANUAL:  #
                #     return
                next_call = self.call_factory.get_call(self._plan, prev_call)
                if next_call.planned_date <= end_date:
                    self.calls.append(next_call)
                else:
                    del next_call
                    break

                prev_call = next_call

    def start_in_cycle(self, start_date: date, start_offset=0):
        pass  # reserved for strategy plan scheduling

    def restart_scheduling(self, start_date: date, del_waiting_calls=True):
        pass

    def cancel_scheduling(self, start_date: date, del_waiting_calls=True):
        pass

    def refresh_calls(self):
        # no adding calls even if updated plan param requires
        end_date = self._plan.scheduling_end_date()
        tmp_list = []
        for c in self.calls:
            c.update()
            if c.planned_date <= end_date or c.status != SS_HOLD:
                tmp_list.append(c)

        self.calls = tmp_list

    # SAP rules:
    # if shedule_period is 0:
    #       when "update scheduling" or "rescheduling" in IP30, a new "Hold" call will be created
    #       if no waiting (Hold or Fixed) call exists, even if planned date exceeds today()
    def update_scheduling(self):
        self.refresh_calls()
        # adding calls if updated plan param requires
        last_scheduled_call = self.get_last_scheduled_call()
        if last_scheduled_call is not None:
            if (self._plan.schedule_period > 0 and
               last_scheduled_call.planned_date < self._plan.scheduling_end_date()):
                self.create_following_calls(last_scheduled_call, self._plan.scheduling_end_date())
            elif last_scheduled_call.status not in [SS_HOLD, SS_FIXED]:
                # always create a new HOLD call
                new_call = self.call_factory.get_call(self._plan, last_scheduled_call)
                self.calls.append(new_call)
        else:
            raise ValueError('Error: in update_scheduling(self)')

    def manual_call(self, sc: Call, plan_date: date):
        data = [self.get_next_manual_call_num(), plan_date.strftime(YYYYMMDD),
                plan_date.strftime(YYYYMMDD), '',  sc.start_date.strftime(YYYYMMDD),
                '', sc.prev_call_num, ST_MANUAL, SS_SAVE_TO_CALL, sc.due_package]
        new_call = self.call_factory.get_call(self._plan, data=data)
        self.calls.append(new_call)

    def release_call(self, sc: Call) -> bool:
        pc = sc.prev_call
        if pc is not None and (pc.status not in [SS_HOLD, SS_FIXED]):
            print('Error: Impossible to release, the previous call status is ' + pc.status)
            return False
        else:
            sc.release()
            return True

    def complete_call(self, sc: Call, comp_date: date) -> bool:
        pc = sc.prev_call
        if sc.status != SS_CALLED:
            print('Error: Impossible to complete, the call is not called')
            return False
        elif pc is not None and pc.status in [SS_HOLD, SS_FIXED]:
            print('Error: Impossible to release, the previous call status is ' + pc.status)
            return False
        else:
            sc.complete(comp_date)
            # SAP rule: after completing a call, automatically call "update scheduling"
            self.update_scheduling()
            return True

    def skip_call(self, sc: Call) -> bool:
        pc = sc.prev_call
        if pc is not None and pc.status in [SS_HOLD, SS_FIXED]:
            print('Error: Impossible to skip, the previous call status is ' + pc.status)
            return False
        else:
            sc.skip()
            return True

    def fix_call(self, sc: Call, fix_date: date, next_call: Call) -> bool:
        pc = sc.prev_call
        if next_call is None:
            next_plan_date = str2Date('20991231')
        else:
            next_plan_date = next_call.planned_date

        if pc is not None and pc.status in [SS_HOLD, SS_FIXED]:
            print('Error: Impossible to fix, the previous call status is ' + pc.status)
            return False
        else:
            if fix_date > pc.planned_date and fix_date < next_plan_date:
                sc.fix(fix_date)
                return True
            else:
                print('Error: Invalid date to fix')
                return False

    def get_last_scheduled_call(self) -> Call:
        call_nums = []
        for s in self.calls:
            if s.scheduling_type != ST_MANUAL:
                call_nums.append(s.call_num)

        if len(call_nums) == 0:
            return None
        else:
            max_num = max(call_nums)
            for s in self.calls:
                if s.call_num == max_num:
                    return s

    def get_next_manual_call_num(self) -> int:
        MANUAL_CALL_NUM_START = 90000000
        maxnum = MANUAL_CALL_NUM_START
        nums = []
        for sch in self.calls:
            if sch.scheduling_type == ST_MANUAL:
                nums.append(sch.call_num)

        if len(nums) > 0:
            maxnum = max(nums) + 1

        return maxnum

    def get_call_list(self) -> list:
        data = []
        for c in self.calls:
            datarow = c.get_call_in_list()
            data.append(datarow)
        return data


class SingleCycleScheduler(Scheduler):
    def __init__(self, p: MaintenancePlan, call_obj_interval=0):
        self.call_factory = SingleCycleCallFactory()
        super().__init__(p, call_obj_interval)


class StrategyScheduler(Scheduler):
    def __init__(self, p: StrategyPlan, call_obj_interval=0):
        self.call_factory = StrategyCallFactory()
        super().__init__(p, call_obj_interval)

    def start_in_cycle(self, start_date: date, start_offset=0):
        self._plan.start_offset = start_offset
        super().start_call(start_date)    
        
        

class TestScheduler:
    _scheduler = None

    def __init__(self, builder):
        self._builder = builder
        self._scheduler = builder.build_scheduler()
        print('\n-----after schedule loaded------')
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_refresh_calls(self):
        self._scheduler.refresh_calls()
        print('\n-----after refresh_calls------')
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_start_scheduling(self):
        sd = datetime.today().date() + timedelta(days=-30)
        self._scheduler.start_scheduling(sd)
        print('\n-----after start_scheduling------')
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_manual_call(self):
        sd = datetime.today().date()
        self._scheduler.manual_call(self._scheduler.calls[1], sd)
        sd = datetime.today().date() + timedelta(days=10)
        self._scheduler.manual_call(self._scheduler.calls[2], sd)
        print('\n-----after manual call------')
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_fix_call(self):
        c = self._scheduler.calls[1]
        self._scheduler.fix_call(c, str2Date('20230725'), self._scheduler.calls[2])
        print('\n-----after fix------')
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_skip_call(self):
        print('\n-----after skip------')
        self._scheduler.skip_call(self._scheduler.calls[1])
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_complete_call(self):
        if len(self._scheduler.calls) > 0:
            c = self._scheduler.calls[0]
            self._scheduler.complete_call(c, str2Date('20230625'))
            print('\n-----after complete------')
            df = pandas.DataFrame(self._scheduler.get_call_list())
            print(df)

    def test_update_scheduling(self):
        self._scheduler.update_scheduling()
        print('\n-----after update_scheduling------')
        df = pandas.DataFrame(self._scheduler.get_call_list())
        print(df)

    def test_save(self):
        self._scheduler.save_to_DB()
        print('\n-----saved successfully!------')

    def test_all(self):
        self.test_refresh_calls()
        self.test_start_scheduling()
        self.test_fix_call()
        self.test_skip_call()
        self.test_manual_call()

        # self.test_save()
        self.test_complete_call()
        # self.test_update_scheduling()
        # self.test_save

    def test_load_and_complete(self):
        self.test_refresh_calls()
        self.test_complete_call()

    def test_new_start(self):
        self._clear_calls()
        self.test_refresh_calls()
        self.test_start_scheduling()

    def test_load_and_start(self):
        self.test_refresh_calls()
        self.test_start_scheduling()

    def _clear_calls(self):
        self._scheduler.calls = []


class SchedulerBuilder:
    def build_scheduler(self) -> Scheduler:
        return None


class SingleCycleSchedulerBuilder(SchedulerBuilder):
    def build_scheduler(self):
        plan_data = {
            'plan_num': '1000007',
            'cycle': 1, 'cycle_unit': 'MON',
            'offset': 0,
            'SF_late': 100,
            'SF_late_tolerance': 10,
            'SF_early': 100,
            'SF_early_tolerance': 10,
            'cycle_change_factor': 1,
            'call_horizon': 50,
            'schedule_period': 90, 'sp_unit': 'D',
            'completion_requirement': False,
            'start_date': '20230601',
            'scheduling_indicator': SI_TIME,
            'factory_calendar': '00'}
        _plan = MaintenancePlan(plan_data)
        return SingleCycleScheduler(_plan)


class ZeroSchedulingPeriodBuilder(SchedulerBuilder):
    def build_scheduler(self):
        plan_data = {
            'plan_num': '1000008',
            'cycle': 1, 'cycle_unit': 'MON',
            'offset': 0,
            'SF_late': 0,
            'SF_late_tolerance': 0,
            'SF_early': 0,
            'SF_early_tolerance': 0,
            'cycle_change_factor': 1,
            'call_horizon': 0,
            'schedule_period': 0, 'sp_unit': 'D',
            'completion_requirement': True,
            'start_date': '20230601',
            'scheduling_indicator': SI_TIME,
            'factory_calendar': '00'}
        _plan = MaintenancePlan(plan_data)
        return SingleCycleScheduler(_plan)



class StrategySchedulerBuilder(SchedulerBuilder):
    def build_scheduler(self):
        plan_data = {
            'plan_num': '1000003',
            'cycle': 30, 'cycle_unit': 'D',
            'offset': 0,
            'SF_late': 0,
            'SF_late_tolerance': 0,
            'SF_early': 0,
            'SF_early_tolerance': 0,
            'cycle_change_factor': 1,
            'call_horizon': 100,
            'schedule_period': 12, 'sp_unit': 'MON',
            'completion_requirement': False,
            'start_date': '20230601',
            'scheduling_indicator': SI_KEY_DATE,
            'factory_calendar': '00'}
        strategy_head = ["A", "Scheduling by time", 0, "MON", 0, 0, 0, 0, 0, ""]
        package_data = [
            [1, 2, "MON", "2-monthly", "2M", 1, "H1", 0, "", 2, 2, True],
            [2, 3, "MON", "3-monthly", "3M", 2, "H2", 0, "", 5, 5, True],
            [3, 5, "MON", "5-monthly", "5M", 3, "H3", 0, "", 10, 10, True]]
        ms = MaintenanceStrategy(strategy_head, package_data)
        _plan = StrategyPlan(plan_data, ms)
        # print(type(self), _plan, '    ', _plan.cycle_in_days(), 'days')

        p = []
        d = ms.package_sequence(0, 360)
        for r in d:
            sss = str(r[0]) + ': '
            for i in range(len(r[1])):
                p = ms.get_package(r[1][i])
                sss += p.cycle_short_text
            print(sss)

        return StrategyScheduler(_plan)        
    
    

def main():
    print('\n\n===============test_new_start=====================')
    builder = SingleCycleSchedulerBuilder()
    test = TestScheduler(builder)
    test.test_new_start()
    # test.test_save()

    print('\n\n==============test_none zero scheduling period======================')
    builder = SingleCycleSchedulerBuilder()
    test = TestScheduler(builder)
    test.test_load_and_complete()

    print('\n\n==============test zero scheduling period======================')
    builder = ZeroSchedulingPeriodBuilder()
    test = TestScheduler(builder)
    # test.test_start_scheduling()
    # test.test_save()
    test.test_load_and_complete()

    print('\n\n==============test strategy scheduling: start======================')
    builder = StrategySchedulerBuilder()
    test = TestScheduler(builder)
    test.test_all()

    print('\n\n==============test strategy scheduling: start in cycle======================')
    test._scheduler._plan.start_offset = 120
    print('start offset: ', test._scheduler._plan.start_offset)
    builder = StrategySchedulerBuilder()
    test = TestScheduler(builder)
    test.test_all()


if __name__ == "__main__":
    main()
    
