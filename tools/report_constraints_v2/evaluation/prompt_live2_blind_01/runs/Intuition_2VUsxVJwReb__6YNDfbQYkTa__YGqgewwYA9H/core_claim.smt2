; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun valid_until () Int)
(declare-fun valid_after () Int)
(declare-fun execution_time () Int)
(declare-fun suffix_in_digest () Bool)
(declare-fun attacker_can_intercept () Bool)
(assert
 (= valid_until valid_until))
(assert
 (= valid_after valid_after))
(assert
 (= execution_time execution_time))
(assert
 (= suffix_in_digest suffix_in_digest))
(assert
 (= attacker_can_intercept attacker_can_intercept))
(define-fun report_preconditions () Bool (and (< valid_after valid_until) (not suffix_in_digest) attacker_can_intercept))
(define-fun report_safety () Bool (=> (and (< valid_after valid_until)
         (not suffix_in_digest)
         attacker_can_intercept)
    (and (>= execution_time valid_after) (<= execution_time valid_until))))
(define-fun report_effects () Bool (and (< valid_after valid_until)
     (not suffix_in_digest)
     attacker_can_intercept
     (not (and (>= execution_time valid_after) (<= execution_time valid_until)))))
