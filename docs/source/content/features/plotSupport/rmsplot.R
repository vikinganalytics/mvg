## Publication quality plot for RMS documentation

## Data from VA-Charlie
## assuming wd to be in plotSupport
ts1 <- fread("../../../../../../va-data-charlie/charlieDb/acc/u0001/1570186860.csv")
ts1[,sample:=.I]
ts1[,acceleration:=V1]
ts1[,V1:=NULL]

## Select part of it
nSamples = 4000
accD <- ts1[1:nSamples]

## Calc RMS
rms = sqrt(sum(accD$acceleration^2)/nSamples)

## Plot
plot(x=accD$sample,
     y=accD$acceleration,
     type="l",
     col="blue",
     xlab="sample number",
     ylab="acceleration [g]",
     main = "Root Mean Square of Vibration Samples",
     cex.main=1.5,
     cex.axis=1.5,
     cex.lab=1.5)
abline(h=rms,col="red",lwd=2)
legend("topleft",lty=1,lwd=2,col=c("blue","red"),legend=c("acceleration", "RMS"))
