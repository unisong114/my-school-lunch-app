import {
  Button,
  Field,
  Input,
  MessageBar,
  MessageBarBody,
  Spinner,
  makeStyles,
} from "@fluentui/react-components";
import { CalendarSearchRegular } from "@fluentui/react-icons";

const useStyles = makeStyles({
  row: { display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "flex-end" },
  field: { minWidth: "160px" },
});

interface DateRangePickerProps {
  fromDate: string;
  toDate: string;
  onFromChange: (value: string) => void;
  onToChange: (value: string) => void;
  onSubmit: () => void;
  disabled: boolean;
  loading: boolean;
  validationError: string | null;
}

export function DateRangePicker({
  fromDate,
  toDate,
  onFromChange,
  onToChange,
  onSubmit,
  disabled,
  loading,
  validationError,
}: DateRangePickerProps) {
  const styles = useStyles();

  return (
    <section aria-label="날짜 범위 선택">
      <div className={styles.row}>
        <Field
          className={styles.field}
          label="시작일"
          validationState={validationError ? "error" : "none"}
        >
          <Input
            type="date"
            aria-label="시작일"
            value={fromDate}
            onChange={(_, data) => onFromChange(data.value)}
          />
        </Field>
        <Field
          className={styles.field}
          label="종료일"
          validationState={validationError ? "error" : "none"}
        >
          <Input
            type="date"
            aria-label="종료일"
            value={toDate}
            onChange={(_, data) => onToChange(data.value)}
          />
        </Field>
        <Button
          appearance="primary"
          onClick={onSubmit}
          disabled={disabled || loading}
          icon={loading ? <Spinner size="tiny" /> : <CalendarSearchRegular />}
        >
          급식 조회
        </Button>
      </div>

      {validationError && (
        <MessageBar intent="error" style={{ marginTop: 12 }}>
          <MessageBarBody>{validationError}</MessageBarBody>
        </MessageBar>
      )}
    </section>
  );
}
