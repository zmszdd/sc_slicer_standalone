; REPORT SPEC ONLY: no code transition T; no consistency verdict.
; Int = mathematical integer; address = uninterpreted identity.
; Textual assumptions are NOT silently asserted. Bind them explicitly in stage 3.
; benchmark generated from python API
(set-info :status unknown)
(declare-fun cd0a96269_downstream_received_poisoned_baseline () Bool)
(declare-fun cd0a96269_oracle_query_failed () Bool)
(declare-fun cd0a96269_returned_center_price () Int)
(declare-fun cd0a96269_twap_window_expired_flag () Bool)
(declare-fun cd0a96269_validated_center_price () Int)
(assert
 (= cd0a96269_downstream_received_poisoned_baseline cd0a96269_downstream_received_poisoned_baseline))
(assert
 (= cd0a96269_oracle_query_failed cd0a96269_oracle_query_failed))
(assert
 (= cd0a96269_returned_center_price cd0a96269_returned_center_price))
(assert
 (= cd0a96269_twap_window_expired_flag cd0a96269_twap_window_expired_flag))
(assert
 (= cd0a96269_validated_center_price cd0a96269_validated_center_price))
(define-fun report_preconditions () Bool (and cd0a96269_twap_window_expired_flag cd0a96269_oracle_query_failed))
(define-fun report_safety () Bool (=> cd0a96269_downstream_received_poisoned_baseline
    (=> (or cd0a96269_twap_window_expired_flag cd0a96269_oracle_query_failed)
        (= cd0a96269_returned_center_price cd0a96269_validated_center_price))))
(define-fun report_effects () Bool (and cd0a96269_downstream_received_poisoned_baseline
     (or cd0a96269_twap_window_expired_flag cd0a96269_oracle_query_failed)
     (not (= cd0a96269_returned_center_price cd0a96269_validated_center_price))))
