; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd0bc7b35_creation_time () Int)
(declare-fun cd0bc7b35_duration () Int)
(declare-fun cd0bc7b35_end_timestamp () Int)
(declare-fun cd0bc7b35_start_in_distant_past () Bool)
(declare-fun cd0bc7b35_start_timestamp () Int)
(assert
 (= cd0bc7b35_creation_time cd0bc7b35_creation_time))
(assert
 (= cd0bc7b35_duration cd0bc7b35_duration))
(assert
 (= cd0bc7b35_end_timestamp cd0bc7b35_end_timestamp))
(assert
 (= cd0bc7b35_start_in_distant_past cd0bc7b35_start_in_distant_past))
(assert
 (= cd0bc7b35_start_timestamp cd0bc7b35_start_timestamp))
(define-fun report_preconditions () Bool (= 0 cd0bc7b35_start_timestamp))
(define-fun report_safety () Bool (=> (= cd0bc7b35_end_timestamp (+ cd0bc7b35_start_timestamp cd0bc7b35_duration))
    (=> cd0bc7b35_start_in_distant_past
        (>= cd0bc7b35_start_timestamp cd0bc7b35_creation_time))))
(define-fun report_effects () Bool (and (= cd0bc7b35_end_timestamp
        (+ cd0bc7b35_start_timestamp cd0bc7b35_duration))
     cd0bc7b35_start_in_distant_past
     (not (>= cd0bc7b35_start_timestamp cd0bc7b35_creation_time))))
(assert report_preconditions)
(assert (not report_safety))
(check-sat)
(get-model)
