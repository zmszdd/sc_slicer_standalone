; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun physical_balance () Int)
(declare-fun total_liabilities () Int)
(declare-fun fot_deposit_received () Int)
(declare-fun standard_deposit_received () Int)
(assert
 (= physical_balance physical_balance))
(assert
 (= total_liabilities total_liabilities))
(assert
 (= fot_deposit_received fot_deposit_received))
(assert
 (= standard_deposit_received standard_deposit_received))
(define-fun report_preconditions () Bool (and (= 990 fot_deposit_received)
     (= 1000 standard_deposit_received)
     (= 1990 physical_balance)
     (= 2000 total_liabilities)))
(define-fun report_safety () Bool (=> (and (= 990 fot_deposit_received) (= 1000 standard_deposit_received))
    (<= total_liabilities physical_balance)))
(define-fun report_effects () Bool (and (= 990 fot_deposit_received)
     (= 1000 standard_deposit_received)
     (not (<= total_liabilities physical_balance))))
