; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun position_in_range () Bool)
(declare-fun fee_charged_high () Bool)
(declare-fun fee_charged_nominal () Bool)
(declare-fun current_tick_manipulated () Bool)
(declare-fun within_safe_mode () Bool)
(assert
 (= position_in_range position_in_range))
(assert
 (= fee_charged_high fee_charged_high))
(assert
 (= fee_charged_nominal fee_charged_nominal))
(assert
 (= current_tick_manipulated current_tick_manipulated))
(assert
 (= within_safe_mode within_safe_mode))
(define-fun report_preconditions () Bool (and position_in_range
     (not position_in_range)
     (not current_tick_manipulated)
     current_tick_manipulated
     within_safe_mode))
(define-fun report_safety () Bool (=> (and position_in_range current_tick_manipulated within_safe_mode)
    (and fee_charged_high (not fee_charged_nominal))))
(define-fun report_effects () Bool (and position_in_range
     current_tick_manipulated
     within_safe_mode
     (not (and fee_charged_high (not fee_charged_nominal)))))
